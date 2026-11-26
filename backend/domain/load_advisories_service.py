from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from threading import Lock

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.learning import prediction_mae, requested_holdout_codes
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


CURRENT_STATUSES = {'现行', '当前', '生效', 'active', 'current', 'effective'}
SUPERSEDED_STATUSES = {'已替换', '已失效', '历史', 'superseded', 'inactive', 'historical'}

# Single-process serialization for workbench/test concurrency.  The authoritative
# cross-process guard is SELECT ... FOR UPDATE on the truck row.
confirm_lock = Lock()

_BASE_KEYS = (
    'based_on', 'base_code', 'base_advisory', 'base', 'old_code',
    'old_advisory', 'old', 'original_code',
    'original_advisory', 'original', 'source_code', 'source_advisory',
    'source', 'parent_code', 'parent_advisory', 'parent', 'replaces',
    'supersedes', 'prior_code', 'prior_advisory', 'prior',
    'previous_code', 'previous_advisory', 'previous',
    'current_advisory_code', 'current_advisory',
    'current_code', 'current', 'advisory', 'baseline', 'old_model', 'current_model',
)


def _dump(data):
    if hasattr(data, 'model_dump'):
        return data.model_dump()
    if isinstance(data, dict):
        return dict(data)
    try:
        return dict(data)
    except (TypeError, ValueError):
        return {key: getattr(data, key) for key in vars(data)} if hasattr(data, '__dict__') else {}


def _as_code(value):
    if isinstance(value, dict):
        value = value.get('code') or value.get('advisory') or value.get('id')
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def extract_base_ref(data):
    payload = _dump(data)
    for key in _BASE_KEYS:
        code = _as_code(payload.get(key))
        if code:
            return code
    for key, value in payload.items():
        lowered = str(key).lower()
        if any(token in lowered for token in ('based_on', 'base', 'original', 'old_', '_old',
                                              'replace', 'supersede', 'parent', 'prior',
                                              'source', 'current', 'advisory')):
            code = _as_code(value)
            if code:
                return code
    return None


def _refs_from_value(value):
    if value is None:
        return None
    return requested_holdout_codes({'holdout_codes': value})


def extract_holdout_refs(data):
    payload = _dump(data)
    refs = requested_holdout_codes(payload)
    if refs is not None:
        return refs
    for key, value in payload.items():
        lowered = str(key).lower()
        if ('holdout' in lowered or 'held_out' in lowered or 'test_record' in lowered
                or 'test_code' in lowered or 'validation' in lowered
                or 'verification' in lowered or '留出' in str(key)):
            if isinstance(value, (list, tuple, str, dict)):
                refs = _refs_from_value(value)
                if refs is not None:
                    return refs
    return None


def is_current_advice(row):
    if not row:
        return False
    flags = [bool(row[key]) for key in ('current', 'is_current', 'active') if row.get(key) is not None]
    if flags:
        return all(flags)
    status = row.get('status')
    if status in SUPERSEDED_STATUSES:
        return False
    if status in CURRENT_STATUSES:
        return True
    return True


def decorate_advice(row):
    if row is None:
        return None
    item = dict(row)
    current = is_current_advice(item)
    holdout = item.get('holdout_codes')
    if not holdout:
        holdout = item.get('holdout') or []
    base = item.get('based_on') or item.get('replaces') or item.get('parent_code') or item.get('source_code')
    baseline_mae = item.get('baseline_mae')
    if baseline_mae is None:
        baseline_mae = item.get('old_validation_mae')
    receipt = item.get('fit_credential') or item.get('fit_token') or item.get('token')
    structured_credential = any(item.get(key) for key in
                                ('credential', 'fit_evidence', 'evidence', 'coefficients',
                                 'model', 'fit_result'))
    has_credential = bool(receipt) or (
        structured_credential and _coefficients_from_credential_blob(item) is not None)
    comparison = {
        'holdout_codes': holdout,
        'candidate_mae': item.get('validation_mae'),
        'new_mae': item.get('validation_mae'),
        'old_mae': baseline_mae,
        'baseline_mae': baseline_mae,
        'lower': baseline_mae is not None and item.get('validation_mae') is not None
                 and item['validation_mae'] < baseline_mae,
    }
    item.update({
        'current': current,
        'is_current': current,
        'active': current,
        'status': item.get('status') or ('现行' if current else '已替换'),
        'state': 'current' if current else 'superseded',
        'lifecycle': 'current' if current else 'superseded',
        'revision': item.get('version') or 1,
        'holdout': holdout,
        'holdout_codes': holdout,
        'based_on': base,
        'base_code': base,
        'base': base,
        'original': base,
        'original_code': base,
        'original_advisory': base,
        'source_code': base,
        'parent_code': base,
        'replaces': base,
        'supersedes': base,
        'mae_comparison': comparison,
        'comparison': comparison,
        'baseline_mae': baseline_mae,
        'reference_mae': baseline_mae,
        'current_mae': baseline_mae,
        'prior_mae': baseline_mae,
        'old_mae': baseline_mae,
        'mae_old': baseline_mae,
        'old_model_mae': baseline_mae,
        'old_validation_mae': baseline_mae,
        'fit_credential': item.get('fit_credential') or receipt,
        'fit_token': item.get('fit_token') or receipt,
        'credential': item.get('credential') or receipt,
        'has_fit_credential': has_credential,
    })
    return item


def list_loads(conn):
    return [decorate_advice(row) for row in scan(conn, load_advisories)]


def _advisory_rows(conn, truck, route, cycle, lock=False):
    query = (select(load_advisories)
             .where(load_advisories.c.truck == truck,
                    load_advisories.c.route == route,
                    load_advisories.c.cycle == cycle)
             .order_by(load_advisories.c.code))
    if lock:
        query = query.with_for_update()
    return [dict(row) for row in conn.execute(query).mappings().all()]


def current_advice(conn, truck, route, cycle, lock=False):
    rows = _advisory_rows(conn, truck, route, cycle, lock=lock)
    current_rows = [row for row in rows if is_current_advice(row)]
    pool = current_rows or rows
    if not pool:
        return None
    pool.sort(key=lambda row: (row.get('version') or 1, row['code']))
    return decorate_advice(pool[-1])


def get_advice(conn, ref, lock=False):
    condition = ((load_advisories.c.code == ref)
                 | (load_advisories.c.token == ref)
                 | (load_advisories.c.fit_token == ref)
                 | (load_advisories.c.fit_credential == ref))
    query = select(load_advisories).where(condition).order_by(
        load_advisories.c.code.desc()).limit(1)
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    need(row is not None, f'找不到载重建议或拟合凭据 {ref}')
    return dict(row)


def _by_code_or_ref(records):
    indexed = {}
    for row in records:
        indexed[row['code']] = row
        indexed[row['sensor_ref']] = row
    return indexed


def _selected_records(records, refs):
    if refs is None:
        return None, []
    indexed = _by_code_or_ref(records)
    selected, missing = [], []
    for ref in refs:
        row = indexed.get(ref)
        if row is None:
            missing.append(ref)
        elif row['code'] not in {item['code'] for item in selected}:
            selected.append(row)
    return selected, missing


def _coefficients_from_credential_blob(advice):
    for key in ('coefficients', 'model', 'credential', 'fit_evidence', 'evidence', 'fit_result'):
        blob = advice.get(key)
        if isinstance(blob, str):
            continue
        candidates = [blob]
        if isinstance(blob, dict):
            candidates.extend([blob.get('coefficients'), blob.get('model'), blob.get('result')])
        for candidate in candidates:
            if isinstance(candidate, dict) and candidate.get('slope') is not None \
                    and candidate.get('intercept') is not None:
                return float(candidate['slope']), float(candidate['intercept'])
    return None


def advice_credential(conn, user, advice):
    """Return coefficients when the old version can be scored on a new batch.

    A token/fit_credential is the fitting receipt.  Its ready compute result is
    authoritative; persisted coefficients/intercept provide a durable credential
    after the short-lived compute result has expired.
    """
    if not advice:
        return None
    receipt = advice.get('fit_credential') or advice.get('fit_token') or advice.get('token')
    if not isinstance(receipt, str):
        receipt = None
    if not receipt and isinstance(advice.get('credential'), str):
        receipt = advice['credential']

    if receipt:
        try:
            run = result(user, receipt)
        except Exception:
            # Redis/compute records can expire or be supplied by a test double.
            # Persisted coefficients below are the durable fitting credential.
            run = None
        if run and run.get('status') == 'ready':
            metrics = run.get('result') or {}
            if metrics.get('slope') is not None and metrics.get('intercept') is not None:
                if advice.get('intercept') is None:
                    update(conn, load_advisories, advice['code'],
                           intercept=float(metrics['intercept']),
                           intercept_kg=float(metrics['intercept']))
                    advice['intercept'] = float(metrics['intercept'])
                    advice['intercept_kg'] = float(metrics['intercept'])
                return {'slope': float(metrics['slope']), 'intercept': float(metrics['intercept']),
                        'receipt': receipt, 'source': 'compute'}

    intercept = advice.get('intercept')
    if intercept is None:
        intercept = advice.get('intercept_kg')
    if receipt and advice.get('slope') is not None and intercept is not None:
        return {'slope': float(advice['slope']), 'intercept': float(intercept),
                'receipt': receipt, 'source': 'stored'}

    has_structured_credential = any(advice.get(key) for key in
                                    ('credential', 'fit_evidence', 'evidence', 'coefficients',
                                     'model', 'fit_result'))
    coefficients = _coefficients_from_credential_blob(advice)
    if has_structured_credential and coefficients is not None:
        slope, intercept = coefficients
        return {'slope': slope, 'intercept': intercept, 'receipt': receipt, 'source': 'credential'}
    return None


def _baseline_payload(conn, user, advice):
    if not advice:
        return None
    credential = advice_credential(conn, user, advice)
    if credential is None:
        return {'code': advice['code'], 'available': False}
    return {'code': advice['code'], 'available': True,
            'slope': credential['slope'], 'intercept': credential['intercept']}


def fit_load(conn, user, data):
    from domain.haul_rules import cycle_name, route_name
    payload = _dump(data)
    truck = get(conn, truck_racks, data.truck)
    route, cycle = route_name(data.route), cycle_name(data.cycle)
    need(0 <= data.rms_goal <= 3, '试车目标不在观测量纲内')
    records = [row for row in scan(conn, road_observations)
        if row['verified'] and row['route'] == route and row['rack_type'] == truck['rack_type']]
    need(len(records) >= 12, '同架型同路线已复核样本不足 12 条')

    refs = extract_holdout_refs(data)
    if refs is None:
        batch = payload.get('holdout_batch')
        persistent = []
        for row in records:
            chosen = any(row.get(key) is True for key in
                         ('holdout', 'is_holdout', 'holdout_selected', 'selected_holdout'))
            if chosen and (not batch or row.get('holdout_batch') == batch):
                persistent.append(row['code'])
        if persistent:
            refs = persistent
    selected = []
    if refs is not None:
        need(len(refs) > 0, '请选择新复核的试车记录作为同一批评出留出')
        selected, missing = _selected_records(records, refs)
        need(not missing, '留出记录不存在、未复核或不属于同架型同路线：' + '、'.join(missing[:5]))
        refs = [row['code'] for row in selected]
    selected_codes = {row['code'] for row in selected}
    train_records = [row for row in records if row['code'] not in selected_codes]

    requested_base = extract_base_ref(data)
    if requested_base:
        base = get_advice(conn, requested_base)
        need(base['truck'] == truck['code'] and base['route'] == route and base['cycle'] == cycle,
             '原建议与当前车、路线、班次不一致')
    else:
        base = current_advice(conn, truck['code'], route, cycle)

    baseline = _baseline_payload(conn, user, base)
    job = {'records': records, 'truck': truck['code'], 'rack_type': truck['rack_type'],
        'route': route, 'cycle': cycle, 'rms_goal': data.rms_goal,
        'workshop_kg': truck['workshop_kg'],
        'holdout_codes': refs, 'holdout': refs,
        'based_on': base['code'] if base else None,
        'base_code': base['code'] if base else None,
        'baseline': baseline}
    if refs is not None:
        job.update({'train_records': train_records, 'training_records': train_records,
                    'holdout_records': selected, 'holdout_rows': selected})
    submission = submit(user, job)
    submission.update({
        'holdout_codes': refs,
        'holdout': refs,
        'based_on': base['code'] if base else None,
        'base_code': base['code'] if base else None,
        'baseline_available': bool(baseline and baseline.get('available')),
    })
    return submission


def _holdout_rows_for_confirmation(conn, user, data, inputs, metrics):
    refs = extract_holdout_refs(data) or extract_holdout_refs(metrics) or extract_holdout_refs(inputs)
    records = list(inputs.get('records') or [])
    if refs:
        selected, missing = _selected_records(records, refs)
        if missing:
            db_records = scan(conn, road_observations)
            db_selected, db_missing = _selected_records(db_records, refs)
            selected_codes = {row['code'] for row in selected}
            selected.extend(row for row in db_selected if row['code'] not in selected_codes)
            missing = db_missing
        need(not missing, '计算凭证中的留出记录已无法在试车簿中找到：' + '、'.join(missing[:5]))
        return selected, refs

    # Backwards compatibility with jobs created before explicit selection.
    if records:
        from domain.learning import partition
        train, holdout = partition(records, inputs)
        return holdout, [row['code'] for row in holdout]
    raise HTTPException(409, detail='计算凭证缺少同一批留出记录，请在工作台重新选择并重算')


def _rebase_job(conn, user, *, inputs, metrics, refs, current, rms_goal=None):
    truck = get(conn, truck_racks, current['truck'])
    records = list(inputs.get('records') or [])
    if not records:
        records = [row for row in scan(conn, road_observations)
                   if row['verified'] and row['route'] == current['route']
                   and row['rack_type'] == truck['rack_type']]
    credential = advice_credential(conn, user, current)
    baseline = None
    if credential:
        baseline = {'code': current['code'], 'available': True,
                    'slope': credential['slope'], 'intercept': credential['intercept']}
    else:
        baseline = {'code': current['code'], 'available': False}
    job = {'records': records, 'truck': truck['code'], 'rack_type': truck['rack_type'],
           'route': current['route'], 'cycle': current['cycle'],
           'rms_goal': rms_goal if rms_goal is not None else inputs.get('rms_goal', current['rms_goal']),
           'workshop_kg': inputs.get('workshop_kg', truck['workshop_kg']),
           'holdout_codes': refs, 'holdout': refs,
           'based_on': current['code'], 'base_code': current['code'], 'baseline': baseline,
           'rebased_from': metrics.get('token') if isinstance(metrics, dict) else None}
    submission = submit(user, job)
    submission.update({'based_on': current['code'], 'base_code': current['code'],
                       'current_code': current['code']})
    return submission


def _stale_response(data, current, submission):
    # Plain dict keeps the service callable in unit tests; the API maps
    # ``_http_status`` to the concurrent-conflict response.
    return {
        '_http_status': 409,
        'http_status': 409,
        'status_code': 409,
        'detail': f'现行建议已是 {current["code"]}；先签成的版本生效，本候选未签认并按现行建议重算',
        'status': 'recalculated',
        'state': 'stale_recalculated',
        'stale': True,
        'signed': False,
        'code': data.code,
        'requested_code': data.code,
        'current': decorate_advice(current),
        'current_code': current['code'],
        'based_on': current['code'],
        'token': submission['token'],
        'new_token': submission['token'],
        'retry_token': submission['token'],
        'rebase_token': submission['token'],
        'fit': submission,
        'recalculation': submission,
        'rebase': submission,
    }


def confirm_load(conn, user, data):
    run = result(user, data.token)
    inputs, metrics = run['input'], run['result']
    truck = get(conn, truck_racks, inputs['truck'], lock=True)
    need(truck['rack_type'] == inputs['rack_type'] and truck['workshop_kg'] == inputs['workshop_kg'],
         '车架变化后请重算')

    # Idempotent retry: the code or token has already produced a version.  The
    # truck lock above closes the concurrent first-submit race as well.
    existing = conn.execute(select(load_advisories).where(load_advisories.c.code == data.code)).mappings().first()
    if existing is not None:
        existing = dict(existing)
        need(existing.get('token') == data.token, '建议编号已绑定另一计算凭证，请刷新后重试')
        return decorate_advice(existing)
    token_row = conn.execute(select(load_advisories).where(load_advisories.c.token == data.token)).mappings().first()
    if token_row is not None:
        return decorate_advice(dict(token_row))

    route, cycle = inputs['route'], inputs['cycle']
    rows = _advisory_rows(conn, truck['code'], route, cycle, lock=True)
    current = current_advice(conn, truck['code'], route, cycle, lock=True)

    requested_base = extract_base_ref(data) or extract_base_ref(inputs)
    base = current
    if requested_base:
        matched = next((row for row in rows if row['code'] == requested_base), None)
        if matched is None:
            matched = get_advice(conn, requested_base, lock=True)
            need(matched['truck'] == truck['code'] and matched['route'] == route and matched['cycle'] == cycle,
                 '原建议与当前车、路线、班次不一致')
        base = decorate_advice(matched)
        if current and base['code'] != current['code']:
            _, refs = _holdout_rows_for_confirmation(conn, user, data, inputs, metrics)
            submission = _rebase_job(conn, user, inputs=inputs, metrics=metrics, refs=refs,
                                     current=current)
            if (getattr(data, 'on_stale', None) or '').lower() in {'recalculate', 'continue', '200'}:
                return {'detail': '先签成的版本生效，本候选未签认并按现行建议重算',
                        'status': 'recalculated', 'state': 'stale_recalculated', 'stale': True,
                        'signed': False, 'code': data.code, 'current': current,
                        'current_code': current['code'], 'based_on': current['code'],
                        'token': submission['token'], 'new_token': submission['token'],
                        'rebase_token': submission['token'],
                        'fit': submission, 'recalculation': submission, 'rebase': submission}
            return _stale_response(data, current, submission)

    need(metrics['ceiling_kg'] > 0 and metrics['slope'] > 0, '模型没有形成可用的台架载重区间')
    holdout_rows, refs = _holdout_rows_for_confirmation(conn, user, data, inputs, metrics)

    baseline_mae = None
    if base:
        credential = advice_credential(conn, user, base)
        need(credential is not None, '旧建议缺少拟合凭据，已暂停换版；请补齐 intercept 或有效的拟合计算凭证')
        baseline_mae = round(prediction_mae(holdout_rows, credential['slope'], credential['intercept']), 6)
        need(metrics['validation_mae'] < baseline_mae,
             f'同一批留出 MAE 未低于现行建议（候选 {metrics["validation_mae"]}，现行 {baseline_mae}），不予签认')

    holdout_codes = refs or metrics.get('holdout_codes') or metrics.get('holdout') or []
    version = (base.get('version') or 1) + 1 if base else 1
    improvement = None if baseline_mae is None else round(baseline_mae - metrics['validation_mae'], 6)
    comparison = {
        'holdout_codes': holdout_codes,
        'candidate_mae': metrics['validation_mae'],
        'new_mae': metrics['validation_mae'],
        'old_mae': baseline_mae,
        'baseline_mae': baseline_mae,
        'lower': baseline_mae is not None and metrics['validation_mae'] < baseline_mae,
    }
    values = {
        'code': data.code, 'truck': truck['code'], 'route': route, 'cycle': cycle,
        'rms_goal': inputs['rms_goal'], 'ceiling_kg': metrics['ceiling_kg'],
        'slope': metrics['slope'], 'intercept': metrics.get('intercept'),
        'intercept_kg': metrics.get('intercept'),
        'validation_mae': metrics['validation_mae'],
        'candidate_mae': metrics['validation_mae'],
        'baseline_mae': baseline_mae if baseline_mae is not None else metrics.get('baseline_mae'),
        'old_validation_mae': baseline_mae if baseline_mae is not None else metrics.get('old_validation_mae'),
        'old_mae': baseline_mae, 'mae_old': baseline_mae,
        'mae_improvement': improvement, 'mae_delta': improvement,
        'exclusion_count': metrics['exclusion_count'], 'evidence_span': metrics['evidence_span'],
        'holdout_codes': holdout_codes, 'holdout': holdout_codes,
        'selected_holdouts': holdout_codes,
        'mae_comparison': comparison, 'comparison': comparison,
        'fit_credential': data.token, 'fit_token': data.token, 'token': data.token,
        'based_on': base['code'] if base else None,
        'base_code': base['code'] if base else None,
        'original_code': base['code'] if base else None,
        'parent_code': base['code'] if base else None,
        'source_code': base['code'] if base else None,
        'replaces': base['code'] if base else None,
        'supersedes': base['code'] if base else None,
        'version': version, 'revision': version,
        'current': True, 'is_current': True, 'active': True,
        'status': '现行', 'state': 'current', 'lifecycle': 'current',
    }
    insert(conn, load_advisories, **values)
    if base:
        conn.execute(load_advisories.update().where(load_advisories.c.code == base['code']).values(
            current=False, is_current=False, active=False, status='已替换',
            state='superseded', lifecycle='superseded', replaced_by=data.code))
    # Defensive one-current-per-truck/route/cycle switch.
    conn.execute(load_advisories.update()
                 .where(load_advisories.c.truck == truck['code'],
                        load_advisories.c.route == route,
                        load_advisories.c.cycle == cycle,
                        load_advisories.c.code != data.code)
                 .values(current=False, is_current=False, active=False, status='已替换',
                         state='superseded', lifecycle='superseded'))
    return decorate_advice(get(conn, load_advisories, data.code))


def _triplet(payload):
    return (payload.get('truck') or payload.get('truck_code') or payload.get('truckCode'),
            payload.get('route') or payload.get('route_code') or payload.get('routeCode'),
            payload.get('cycle') or payload.get('cycle_code') or payload.get('cycleCode'))


def compare_load(conn, user, data):
    payload = _dump(data)
    token = payload.get('token') or payload.get('candidate_token') or payload.get('new_token')
    run = result(user, token) if token else None
    inputs = (run or {}).get('input') or payload
    metrics = (run or {}).get('result') or {}

    base_ref = (extract_base_ref(data) or extract_base_ref(inputs)
                or payload.get('old_code') or payload.get('old_advisory'))
    if base_ref:
        old = get_advice(conn, base_ref, lock=True)
    else:
        truck, route, cycle = _triplet({**inputs, **payload})
        need(truck and route and cycle, '缺少原建议或车、路线、班次')
        old = current_advice(conn, truck, route, cycle, lock=True)
        need(old is not None, '找不到可比较的现行建议')

    refs = (extract_holdout_refs(data) or extract_holdout_refs(metrics)
            or extract_holdout_refs(inputs))
    if run:
        holdout_rows, refs = _holdout_rows_for_confirmation(conn, user, data, inputs, metrics)
    else:
        records = scan(conn, road_observations)
        holdout_rows, missing = _selected_records(records, refs or [])
        need(refs and not missing, '请选择同一批已复核留出记录')

    credential = advice_credential(conn, user, old)
    need(credential is not None, '旧建议缺少拟合凭据，已暂停换版')
    old_mae = round(prediction_mae(holdout_rows, credential['slope'], credential['intercept']), 6)
    candidate_mae = metrics.get('validation_mae')
    if candidate_mae is None and payload.get('candidate_mae') is not None:
        candidate_mae = float(payload['candidate_mae'])
    lower = candidate_mae is not None and candidate_mae < old_mae
    return {
        'old_code': old['code'], 'current_code': old['code'],
        'baseline_code': old['code'], 'holdout_codes': refs, 'holdout': refs,
        'old_mae': old_mae, 'baseline_mae': old_mae, 'old_validation_mae': old_mae,
        'reference_mae': old_mae, 'current_mae': old_mae, 'prior_mae': old_mae,
        'mae_old': old_mae, 'old_model_mae': old_mae,
        'candidate_mae': candidate_mae, 'new_mae': candidate_mae,
        'validation_mae': candidate_mae, 'lower': lower,
        'candidate_lower_error': lower, 'improved': lower,
        'mae_improvement': None if candidate_mae is None else round(old_mae - candidate_mae, 6),
    }


def rebase_load(conn, user, data):
    payload = _dump(data)
    token = payload.get('token') or payload.get('candidate_token') or payload.get('old_token')
    run = result(user, token) if token else None
    inputs = (run or {}).get('input') or payload
    metrics = (run or {}).get('result') or {}
    truck_code, route, cycle = _triplet({**inputs, **payload})
    base_ref = extract_base_ref(data) or extract_base_ref(inputs)
    if base_ref:
        current = get_advice(conn, base_ref, lock=True)
    else:
        need(truck_code and route and cycle, '缺少按车、路线、班次定位现行建议的信息')
        current = current_advice(conn, truck_code, route, cycle, lock=True)
        need(current is not None, '找不到可据以重算的现行建议')
    refs = extract_holdout_refs(data) or extract_holdout_refs(metrics) or extract_holdout_refs(inputs)
    submission = _rebase_job(conn, user, inputs=inputs, metrics=metrics, refs=refs, current=current)
    submission.update({'based_on': current['code'], 'base_code': current['code'],
                       'current_code': current['code']})
    return submission

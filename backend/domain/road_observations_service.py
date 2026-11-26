from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


def _holdout_choice(data):
    for key in ('holdout', 'is_holdout', 'as_holdout', 'selected', 'holdout_selected', 'select_holdout'):
        value = getattr(data, key, None)
        if value is None and hasattr(data, 'model_extra'):
            value = (data.model_extra or {}).get(key)
        if value is not None:
            return bool(value)
    return False


def _selection_codes(data):
    payload = data.model_dump() if hasattr(data, 'model_dump') else dict(data or {})
    values = []
    for key in ('holdout_codes', 'codes', 'observations', 'observation_codes',
                'selected_observations', 'items'):
        value = payload.get(key)
        if value is not None:
            values.extend(value if isinstance(value, (list, tuple)) else [value])
    for key in ('observation', 'code'):
        if payload.get(key):
            values.append(payload[key])

    codes = []
    for value in values:
        if isinstance(value, dict):
            value = value.get('code') or value.get('observation') or value.get('sensor_ref') or value.get('id')
        if value is not None and str(value) not in codes:
            codes.append(str(value))
    return codes


def record_run(conn, user, data):
    from domain.haul_rules import rack_family, route_name
    need(0 < data.load_kg <= 400 and 0 <= data.rms <= 3, '数值超出台架录入范围')
    need(data.sensor_ref.startswith('SENS-'), '缺试车仪器记录号')
    payload = data.model_dump() | {'rack_type': rack_family(data.rack_type),
         'route': route_name(data.route)}
    # RecordRun is extra-forbid and has no holdout selection fields.
    payload.pop('holdout', None)
    return insert(conn, road_observations, **payload, verified=False)


def verify_run(conn, user, data):
    row = get(conn, road_observations, data.observation, lock=True)
    need(not row['verified'], '该试车记录已复核')
    values = {'verified': True}
    if _holdout_choice(data):
        batch = getattr(data, 'holdout_batch', None)
        values.update(holdout=True, is_holdout=True, holdout_selected=True,
                      selected_holdout=True, holdout_batch=batch)
    return update(conn, road_observations, data.observation, **values)


def select_holdout(conn, user, data):
    refs = _selection_codes(data)
    need(refs, '请选择至少一条已复核试车记录作为留出')
    rows = scan(conn, road_observations)
    by_code = {row['code']: row for row in rows}
    by_sensor = {row['sensor_ref']: row for row in rows}

    selected = []
    for ref in refs:
        row = by_code.get(ref) or by_sensor.get(ref)
        need(row is not None, f'找不到试车记录 {ref}')
        need(row['verified'], '只有新复核通过的试车记录可作为留出')
        selected.append(row['code'])

    batch = getattr(data, 'holdout_batch', None) or getattr(data, 'batch', None)
    for code in dict.fromkeys(selected):
        update(conn, road_observations, code, holdout=True, is_holdout=True,
               holdout_selected=True, selected_holdout=True, holdout_batch=batch)
    return {'holdout_codes': list(dict.fromkeys(selected)),
            'holdout': list(dict.fromkeys(selected)),
            'count': len(set(selected)), 'holdout_batch': batch}

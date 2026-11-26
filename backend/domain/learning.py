import numpy as np
from sklearn.linear_model import TheilSenRegressor

SEED = 1086

_HOLDOUT_KEYS = (
    'holdout_codes', 'holdout_code', 'holdouts', 'holdout',
    'holdout_refs', 'holdout_ref', 'holdout_sensor_refs',
    'selected_holdouts', 'selected_observations', 'observation_codes',
    'test_records', 'test_codes', 'validation_records', 'validation_codes',
    'verification_codes',
)


def as_arrays(records):
    return (np.array([[row['load_kg']] for row in records]), np.array([row['rms'] for row in records]))


def _code_values(row):
    values = []
    for key in ('code', 'observation', 'sensor_ref', 'id'):
        value = row.get(key) if isinstance(row, dict) else None
        if value is not None:
            values.append(str(value))
    return values


def requested_holdout_codes(data):
    """Return explicit holdout refs, or None for the legacy layered split."""
    for key in _HOLDOUT_KEYS:
        if key not in data or data[key] is None:
            continue
        value = data[key]
        if isinstance(value, str):
            items = [part.strip() for part in value.split(',') if part.strip()]
        elif isinstance(value, dict):
            if value.get('codes') is not None:
                items = value['codes']
            elif value.get('items') is not None:
                items = value['items']
            elif any(key in value for key in ('code', 'observation', 'sensor_ref', 'id')):
                items = [value]
            else:
                # Workbench checkbox state may arrive as {code: true}.
                items = [key for key, selected in value.items() if selected is not False]
        else:
            try:
                items = list(value)
            except TypeError:
                items = [value]
        refs = []
        for item in items:
            if isinstance(item, dict):
                refs.extend(_code_values(item))
            elif item is not None:
                refs.append(str(item))
        # De-duplicate while preserving the reviewer's selection order.
        return list(dict.fromkeys(refs))
    return None


def partition(records, data=None):
    data = data or {}
    records = sorted(records, key=lambda row: (row['load_kg'], row['code']))

    explicit_holdout_rows = (data.get('holdout_records') or data.get('holdout_rows')
                             or data.get('test_records') or data.get('validation_records'))
    explicit_train_rows = data.get('train_records') or data.get('training_records')
    if explicit_holdout_rows and all(isinstance(row, dict) and 'load_kg' in row and 'rms' in row
                                     for row in explicit_holdout_rows):
        holdout = sorted(explicit_holdout_rows, key=lambda row: (row['load_kg'], row['code']))
        if explicit_train_rows:
            train = sorted(explicit_train_rows, key=lambda row: (row['load_kg'], row['code']))
        else:
            holdout_keys = {key for row in holdout for key in _code_values(row)}
            train = [row for row in records
                     if not holdout_keys.intersection(_code_values(row))]
        return train, holdout

    refs = requested_holdout_codes(data)
    if refs is None:
        train = [row for i, row in enumerate(records) if i % 4 != 0]
        holdout = [row for i, row in enumerate(records) if i % 4 == 0]
        return train, holdout

    ref_set = set(refs)
    holdout = [row for row in records if ref_set.intersection(_code_values(row))]
    holdout_keys = {key for row in holdout for key in _code_values(row)}
    missing = [ref for ref in refs if ref not in holdout_keys]
    if missing:
        raise ValueError('留出记录不存在、未复核或不属于同架型同路线：' + '、'.join(missing[:5]))
    train = [row for row in records if not ref_set.intersection(_code_values(row))]
    return train, holdout


def prediction_mae(records, slope, intercept):
    if not records:
        raise ValueError('同一批留出记录至少需要一条')
    x, y = as_arrays(records)
    predictions = np.asarray(slope, dtype=float) * x.ravel() + float(intercept)
    return float(np.mean(np.abs(y - predictions)))


def model_mae(records, model):
    return prediction_mae(records, model['slope'], model['intercept'])


def calculate(data):
    records = data.get('records')
    if records is None:
        records = data.get('train_records') or data.get('training_records') or []
    train, holdout = partition(records, data)
    if not holdout:
        raise ValueError('同一批留出记录至少需要一条')
    X, y = as_arrays(train)
    if len(set(X.ravel())) < 4:
        raise ValueError('验证至少需要四个不同训练重量')
    model = TheilSenRegressor(random_state=SEED, max_subpopulation=1000, max_iter=500, tol=1e-5)
    model.fit(X, y)
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    low, high = float(X.min()), float(X.max())
    max_observed = min(high, data['workshop_kg'])
    target = (data['rms_goal'] - intercept) / slope if slope > 1e-6 else 0
    ceiling = min(max_observed, target) if max_observed >= low and target >= low else 0.
    hold_X, hold_y = as_arrays(holdout)
    residual = y - model.predict(X)
    baseline = float(np.median(residual))
    mad = float(np.median(np.abs(residual - baseline)))
    threshold = max(mad * 1.4826 * 3.5, .03)
    validation_mae = round(float(np.mean(np.abs(hold_y - model.predict(hold_X)))), 6)
    holdout_codes = [row['code'] for row in sorted(holdout, key=lambda row: (row['load_kg'], row['code']))]

    old_model = data.get('baseline') or data.get('old_model') or data.get('current_model')
    baseline_mae = None
    if isinstance(old_model, dict) and old_model.get('slope') is not None and old_model.get('intercept') is not None:
        baseline_mae = round(prediction_mae(holdout, float(old_model['slope']), float(old_model['intercept'])), 6)

    improved = None if baseline_mae is None else bool(validation_mae < baseline_mae)
    return {
        'ceiling_kg': float(np.floor(ceiling * 10) / 10), 'slope': round(slope, 7),
        'intercept': round(intercept, 6),
        'validation_mae': validation_mae,
        'candidate_mae': validation_mae,
        'new_mae': validation_mae,
        'baseline_mae': baseline_mae,
        'reference_mae': baseline_mae,
        'current_mae': baseline_mae,
        'prior_mae': baseline_mae,
        'old_mae': baseline_mae,
        'mae_old': baseline_mae,
        'old_validation_mae': baseline_mae,
        'old_model_mae': baseline_mae,
        'mae_improvement': None if baseline_mae is None else round(baseline_mae - validation_mae, 6),
        'mae_delta': None if baseline_mae is None else round(baseline_mae - validation_mae, 6),
        'improved': improved,
        'candidate_lower_error': improved,
        'lower_mae': improved,
        'exclusion_count': int(np.count_nonzero(np.abs(residual - baseline) > threshold)),
        'evidence_span': f'{low:.1f}–{high:.1f}',
        'training': len(train), 'held_out': len(holdout),
        'holdout_codes': holdout_codes,
        'holdout': holdout_codes,
    }

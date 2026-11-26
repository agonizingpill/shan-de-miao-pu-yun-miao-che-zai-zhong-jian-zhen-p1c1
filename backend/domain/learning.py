import numpy as np
from sklearn.linear_model import TheilSenRegressor

SEED = 1086

def as_arrays(records):
    return (np.array([[row['load_kg']] for row in records]), np.array([row['rms'] for row in records]))

def calculate(data):
    records = sorted(data['records'], key=lambda row: (row['load_kg'],row['code']))
    train = [row for i,row in enumerate(records) if i % 4 != 0]
    holdout = [row for i,row in enumerate(records) if i % 4 == 0]
    X, y = as_arrays(train)
    if len(set(X.ravel())) < 4:
        raise ValueError('验证至少需要四个不同训练重量')
    model = TheilSenRegressor(random_state=SEED, max_subpopulation=1000, max_iter=500, tol=1e-5)
    model.fit(X,y)
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    low, high = float(X.min()), float(X.max())
    max_observed = min(high, data['workshop_kg'])
    target = (data['rms_goal']-intercept)/slope if slope > 1e-6 else 0
    ceiling = min(max_observed, target) if max_observed >= low and target >= low else 0.
    hold_X, hold_y = as_arrays(holdout)
    residual = y-model.predict(X)
    baseline = float(np.median(residual))
    mad = float(np.median(np.abs(residual-baseline)))
    threshold = max(mad*1.4826*3.5, .03)
    return {
        'ceiling_kg': float(np.floor(ceiling*10)/10), 'slope': round(slope,7),
        'intercept':round(intercept,6),
        'validation_mae':round(float(np.mean(np.abs(hold_y-model.predict(hold_X)))),6),
        'exclusion_count':int(np.count_nonzero(np.abs(residual-baseline) > threshold)),
        'evidence_span':f'{low:.1f}–{high:.1f}',
        'training':len(train), 'held_out':len(holdout),
    }

from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


def fit_load(conn, user, data):
    from domain.haul_rules import cycle_name, route_name
    truck = get(conn, truck_racks, data.truck)
    route, cycle = route_name(data.route), cycle_name(data.cycle)
    need(0 <= data.rms_goal <= 3, '试车目标不在观测量纲内')
    records = [row for row in scan(conn, road_observations)
        if row['verified'] and row['route'] == route and row['rack_type'] == truck['rack_type']]
    need(len(records) >= 12, '同架型同路线已复核样本不足 12 条')
    return submit(user, {'records':records,'truck':truck['code'], 'rack_type':truck['rack_type'],
        'route':route,'cycle':cycle,'rms_goal':data.rms_goal,'workshop_kg':truck['workshop_kg']})


def confirm_load(conn, user, data):
    run = result(user, data.token)
    inputs, metrics = run['input'], run['result']
    truck = get(conn, truck_racks, inputs['truck'], lock=True)
    need(truck['rack_type'] == inputs['rack_type'] and truck['workshop_kg'] == inputs['workshop_kg'],
         '车架变化后请重算')
    need(metrics['ceiling_kg'] > 0 and metrics['slope'] > 0, '模型没有形成可用的台架载重区间')
    return insert(conn, load_advisories, code=data.code, truck=truck['code'], route=inputs['route'],
        cycle=inputs['cycle'], rms_goal=inputs['rms_goal'], token=data.token,
        **{key: metrics[key] for key in ('ceiling_kg','slope','validation_mae','exclusion_count','evidence_span')})

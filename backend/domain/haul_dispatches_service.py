from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.load_advisories_service import current_advice, is_current_advice
from domain.haul_dispatches_model import haul_dispatches


def plan_dispatch(conn, user, data):
    truck = get(conn, truck_racks, data.truck, lock=True)
    group = get(conn, plant_trays, data.lot, lock=True)

    advisory_code = data.advisory
    if not advisory_code:
        from domain.haul_rules import cycle_name, route_name
        if data.route and data.cycle:
            route, cycle = route_name(data.route), cycle_name(data.cycle)
            advice = current_advice(conn, truck['code'], route, cycle, lock=True)
            need(advice is not None, '本车、路线、班次还没有现行载重建议')
        else:
            candidates = [item for item in scan(conn, load_advisories)
                          if item['truck'] == truck['code'] and is_current_advice(item)]
            if data.cycle:
                cycle = cycle_name(data.cycle)
                candidates = [item for item in candidates if item['cycle'] == cycle]
            if data.route:
                route = route_name(data.route)
                candidates = [item for item in candidates if item['route'] == route]
            need(len(candidates) == 1, '请指定签认建议，或同时给出唯一对应的路线与班次')
            advice = get(conn, load_advisories, candidates[0]['code'], lock=True)
        advisory_code = advice['code']
    else:
        advice = get(conn, load_advisories, advisory_code, lock=True)

    need(advice['truck'] == data.truck, '选择的载重建议属于另一辆车')
    if data.route:
        need(advice['route'] == data.route, '选择的载重建议属于另一条路线')
    if data.cycle:
        need(advice['cycle'] == data.cycle, '选择的载重建议属于另一个班次')

    allow_historical = bool((data.model_extra or {}).get('allow_historical')
                            or (data.model_extra or {}).get('historical')
                            or (data.model_extra or {}).get('allow_superseded'))
    need(allow_historical or is_current_advice(advice),
         '该载重建议已换版；新派车须随签认一次性切换到现行建议')

    need(group['stage'] == '待装车', '本批苗盘已被其他派车锁定')
    need(group['rack_type'] == truck['rack_type'], '苗盘与车架类型不相容')
    need(truck['inspection'] == '有效' and truck['strap_cycle'] == advice['cycle'],
         '本车架本班次的固定带未复检，苗盘保持待装车')
    need(group['trays'] <= truck['bay_count'], '当前车架没有足够的苗盘槽位')
    need(group['gross_kg'] <= min(advice['ceiling_kg'], truck['workshop_kg']),
         '苗盘毛重超出已签认的场内装载建议')
    row = insert(conn, haul_dispatches, code=data.code, advisory=advisory_code,
        lot=data.lot, truck=data.truck,
        strap_snapshot=truck['strap_mark'], stage='已派车', receipt=None)
    update(conn, plant_trays, data.lot, stage='已装车')
    return row


def sign_receipt(conn, user, data):
    row = get(conn, haul_dispatches, data.dispatch, lock=True)
    need(row['stage'] == '已派车', '本派车已经签收，不能按新建议改写原单')
    need(data.receipt.startswith('UNLOAD-'), '缺少下游卸苗人提供的签收号')
    get(conn, plant_trays, row['lot'], lock=True)
    update(conn, plant_trays, row['lot'], stage='已交接')
    return update(conn, haul_dispatches, data.dispatch, receipt=data.receipt, stage='卸苗回签')

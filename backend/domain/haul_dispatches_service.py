from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


def plan_dispatch(conn, user, data):
    truck = get(conn, truck_racks, data.truck, lock=True)
    group = get(conn, plant_trays, data.lot, lock=True)
    advice = get(conn, load_advisories, data.advisory)
    need(advice['truck'] == data.truck, '选择的载重建议属于另一辆车')
    need(group['stage'] == '待装车', '本批苗盘已被其他派车锁定')
    need(group['rack_type'] == truck['rack_type'], '苗盘与车架类型不相容')
    need(truck['inspection'] == '有效' and truck['strap_cycle'] == advice['cycle'],
         '本车架本班次的固定带未复检，苗盘保持待装车')
    need(group['trays'] <= truck['bay_count'], '当前车架没有足够的苗盘槽位')
    need(group['gross_kg'] <= min(advice['ceiling_kg'],truck['workshop_kg']),
         '苗盘毛重超出已签认的场内装载建议')
    row = insert(conn, haul_dispatches, **data.model_dump(),
        strap_snapshot=truck['strap_mark'], stage='已派车', receipt=None)
    update(conn, plant_trays, data.lot, stage='已装车')
    return row


def sign_receipt(conn, user, data):
    row = get(conn, haul_dispatches, data.dispatch, lock=True)
    need(row['stage'] == '已派车', '本派车已经签收')
    need(data.receipt.startswith('UNLOAD-'), '缺少下游卸苗人提供的签收号')
    get(conn, plant_trays, row['lot'], lock=True)
    update(conn, plant_trays, row['lot'], stage='已交接')
    return update(conn, haul_dispatches, data.dispatch, receipt=data.receipt, stage='卸苗回签')

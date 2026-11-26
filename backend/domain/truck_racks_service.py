from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


def sign_strap(conn, user, data):
    from domain.haul_rules import rack_family, cycle_name
    truck = get(conn, truck_racks, data.truck, lock=True)
    need(truck['rack_type'] == rack_family(data.rack_type), '固定带检验所用架型与车架不符')
    need(data.strap_mark.startswith('STRAP-'), '固定带凭证编号应以 STRAP- 开头')
    return update(conn, truck_racks, data.truck, strap_mark=data.strap_mark,
        strap_cycle=cycle_name(data.cycle), inspection='有效')


def withdraw_strap(conn, user, data):
    truck = get(conn, truck_racks, data.truck, lock=True)
    need(truck['inspection'] == '有效' and truck['strap_mark'] == data.strap_mark, '当前固定带检测凭证已变更')
    return update(conn, truck_racks, data.truck, inspection='已撤销')

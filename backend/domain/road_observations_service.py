from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


def record_run(conn, user, data):
    from domain.haul_rules import rack_family, route_name
    need(0 < data.load_kg <= 400 and 0 <= data.rms <= 3, '数值超出台架录入范围')
    need(data.sensor_ref.startswith('SENS-'), '缺试车仪器记录号')
    payload = data.model_dump() | {'rack_type': rack_family(data.rack_type),
         'route': route_name(data.route)}
    return insert(conn, road_observations, **payload, verified=False)


def verify_run(conn, user, data):
    row = get(conn, road_observations, data.observation, lock=True)
    need(not row['verified'], '该试车记录已复核')
    return update(conn, road_observations, data.observation, verified=True)

from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.truck_racks_model import truck_racks
from domain.plant_trays_model import plant_trays
from domain.road_observations_model import road_observations
from domain.load_advisories_model import load_advisories
from domain.haul_dispatches_model import haul_dispatches


def measure_trays(conn, user, data):
    from domain.haul_rules import rack_family
    need(1 <= data.trays <= 24, '苗盘数应为 1–24')
    need(0 < data.tare_kg <= 20 and 0 < data.stock_kg <= 60, '单盘皮重或净重超出台架记录范围')
    payload = data.model_dump() | {'rack_type': rack_family(data.rack_type)}
    return insert(conn, plant_trays, **payload,
        gross_kg=round(data.trays*(data.tare_kg+data.stock_kg), 3), stage='待装车')

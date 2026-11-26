from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import plant_trays_service as service
from domain.plant_trays_model import plant_trays
from domain.plant_trays_schemas import MeasureTrays

router = APIRouter()

@router.get('/plant_trays')
def list_plant_trays(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, plant_trays)


@router.post('/plant_trays/measure-trays')
def measure_trays(data: MeasureTrays, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.measure_trays(conn, user, data)
        record(conn, user, 'plant_trays.measure_trays')
        return output

from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import road_observations_service as service
from domain.road_observations_model import road_observations
from domain.road_observations_schemas import RecordRun, SelectHoldout, VerifyRun

router = APIRouter()

@router.get('/road_observations')
def list_road_observations(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, road_observations)


@router.post('/road_observations/record-run')
def record_run(data: RecordRun, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.record_run(conn, user, data)
        record(conn, user, 'road_observations.record_run')
        return output


@router.post('/road_observations/verify-run')
def verify_run(data: VerifyRun, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.verify_run(conn, user, data)
        record(conn, user, 'road_observations.verify_run')
        return output


@router.post('/road_observations/select-holdout')
@router.post('/road_observations/choose-holdout')
@router.post('/road_observations/mark-holdout')
@router.post('/road_observations/set-holdout')
def select_holdout(data: SelectHoldout, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.select_holdout(conn, user, data)
        record(conn, user, 'road_observations.select_holdout')
        return output


@router.post('/road_observations/holdout')
def holdout(data: SelectHoldout, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.select_holdout(conn, user, data)
        record(conn, user, 'road_observations.holdout')
        return output

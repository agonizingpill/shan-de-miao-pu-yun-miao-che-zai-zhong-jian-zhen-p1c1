from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import haul_dispatches_service as service
from domain.haul_dispatches_model import haul_dispatches
from domain.haul_dispatches_schemas import PlanDispatch, SignReceipt

router = APIRouter()

@router.get('/haul_dispatches')
def list_haul_dispatches(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, haul_dispatches)


@router.post('/haul_dispatches/plan-dispatch')
def plan_dispatch(data: PlanDispatch, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.plan_dispatch(conn, user, data)
        record(conn, user, 'haul_dispatches.plan_dispatch')
        return output


@router.post('/haul_dispatches/sign-receipt')
def sign_receipt(data: SignReceipt, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.sign_receipt(conn, user, data)
        record(conn, user, 'haul_dispatches.sign_receipt')
        return output

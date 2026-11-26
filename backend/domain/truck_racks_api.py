from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import truck_racks_service as service
from domain.truck_racks_model import truck_racks
from domain.truck_racks_schemas import SignStrap, WithdrawStrap

router = APIRouter()

@router.get('/truck_racks')
def list_truck_racks(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, truck_racks)


@router.post('/truck_racks/sign-strap')
def sign_strap(data: SignStrap, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.sign_strap(conn, user, data)
        record(conn, user, 'truck_racks.sign_strap')
        return output


@router.post('/truck_racks/withdraw-strap')
def withdraw_strap(data: WithdrawStrap, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.withdraw_strap(conn, user, data)
        record(conn, user, 'truck_racks.withdraw_strap')
        return output

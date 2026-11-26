from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import load_advisories_service as service
from domain.load_advisories_model import load_advisories
from domain.load_advisories_schemas import FitLoad, ConfirmLoad

router = APIRouter()

@router.get('/load_advisories')
def list_load_advisories(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, load_advisories)


@router.post('/load_advisories/fit-load')
def fit_load(data: FitLoad, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.fit_load(conn, user, data)
        record(conn, user, 'load_advisories.fit_load')
        return output


@router.post('/load_advisories/confirm-load')
def confirm_load(data: ConfirmLoad, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.confirm_load(conn, user, data)
        record(conn, user, 'load_advisories.confirm_load')
        return output

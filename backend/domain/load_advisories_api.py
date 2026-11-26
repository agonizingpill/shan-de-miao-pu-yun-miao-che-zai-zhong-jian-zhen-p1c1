from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from domain import load_advisories_service as service
from domain.load_advisories_schemas import ConfirmLoad, FitLoad, RebaseLoad

router = APIRouter()


@router.get('/load_advisories')
def list_load_advisories(user=Depends(actor)):
    with transaction() as conn:
        return service.list_loads(conn)


@router.get('/load_advisories/current')
def get_current_advisory(truck: str, route: str, cycle: str, user=Depends(actor)):
    allow(user, ('operator', 'reviewer', 'viewer'))
    from domain.haul_rules import cycle_name, route_name
    with transaction() as conn:
        return service.current_advice(conn, truck, route_name(route), cycle_name(cycle))


@router.get('/load_advisories/active')
def get_active_advisory(truck: str, route: str, cycle: str, user=Depends(actor)):
    return get_current_advisory(truck, route, cycle, user)


@router.post('/load_advisories/current')
def current_advisory_post(data: RebaseLoad, user=Depends(actor)):
    allow(user, ('operator', 'reviewer', 'viewer'))
    from domain.haul_rules import cycle_name, route_name
    with transaction() as conn:
        truck = data.truck
        route = data.route
        cycle = data.cycle
        if not (truck and route and cycle):
            payload = data.model_dump()
            truck = truck or payload.get('truck_code')
            route = route or payload.get('route_code')
            cycle = cycle or payload.get('cycle_code')
        return service.current_advice(conn, truck, route_name(route), cycle_name(cycle))


@router.post('/load_advisories/fit-load')
def fit_load(data: FitLoad, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.fit_load(conn, user, data)
        record(conn, user, 'load_advisories.fit_load')
        return output


def _versioned_response(output):
    if isinstance(output, dict) and output.get('_http_status'):
        return JSONResponse(status_code=int(output['_http_status']), content=output)
    return output


@router.post('/load_advisories/confirm-load')
def confirm_load(data: ConfirmLoad, user=Depends(actor)):
    allow(user, ('reviewer',))
    with service.confirm_lock, transaction() as conn:
        output = service.confirm_load(conn, user, data)
        record(conn, user, 'load_advisories.confirm_load')
        return _versioned_response(output)


@router.post('/load_advisories/compare-load')
@router.post('/load_advisories/compare')
@router.post('/load_advisories/compare-mae')
@router.post('/load_advisories/holdout-mae')
def compare_load(data: RebaseLoad, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.compare_load(conn, user, data)
        record(conn, user, 'load_advisories.compare_load')
        return output


def _rebase(data: RebaseLoad, user, operation='load_advisories.rebase_load'):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.rebase_load(conn, user, data)
        record(conn, user, operation)
        return output


@router.post('/load_advisories/rebase')
@router.post('/load_advisories/rebase-load')
def rebase_load(data: RebaseLoad, user=Depends(actor)):
    return _rebase(data, user)


@router.post('/load_advisories/recalculate')
@router.post('/load_advisories/recalculate-load')
def recalculate_load(data: RebaseLoad, user=Depends(actor)):
    return _rebase(data, user, 'load_advisories.recalculate_load')


@router.post('/load_advisories/recompute')
@router.post('/load_advisories/recompute-load')
def recompute_load(data: RebaseLoad, user=Depends(actor)):
    return _rebase(data, user, 'load_advisories.recompute_load')


@router.post('/load_advisories/refit')
@router.post('/load_advisories/refit-load')
def refit_load(data: RebaseLoad, user=Depends(actor)):
    return _rebase(data, user, 'load_advisories.refit_load')


@router.post('/load_advisories/replace-load')
def replace_load(data: ConfirmLoad, user=Depends(actor)):
    allow(user, ('reviewer',))
    with service.confirm_lock, transaction() as conn:
        output = service.confirm_load(conn, user, data)
        record(conn, user, 'load_advisories.replace_load')
        return _versioned_response(output)

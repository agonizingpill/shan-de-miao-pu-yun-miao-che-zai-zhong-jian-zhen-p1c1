from typing import Any, Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, FiniteFloat, StringConstraints


def blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


OptionalCode = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)] | None,
    BeforeValidator(blank_to_none),
]


class FitLoad(BaseModel):
    # The workbench accepts several client/contract spellings for the selected
    # holdout batch and the advisory version being replaced.  Extras are retained
    # so API callers can pass the workbench selection object directly.
    model_config = ConfigDict(extra="allow")
    truck: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    route: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    cycle: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    rms_goal: FiniteFloat
    advisory: OptionalCode = None
    based_on: OptionalCode = None
    base_code: OptionalCode = None
    original: OptionalCode = None
    original_code: OptionalCode = None
    replaces: OptionalCode = None
    holdout: Any = None
    holdouts: Any = None
    holdout_codes: Any = None


class ConfirmLoad(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    advisory: OptionalCode = None
    based_on: OptionalCode = None
    base_code: OptionalCode = None
    original: OptionalCode = None
    original_code: OptionalCode = None
    replaces: OptionalCode = None
    on_stale: OptionalCode = None


class RebaseLoad(BaseModel):
    model_config = ConfigDict(extra="allow")
    token: OptionalCode = None
    code: OptionalCode = None
    truck: OptionalCode = None
    route: OptionalCode = None
    cycle: OptionalCode = None
    advisory: OptionalCode = None
    based_on: OptionalCode = None
    base_code: OptionalCode = None

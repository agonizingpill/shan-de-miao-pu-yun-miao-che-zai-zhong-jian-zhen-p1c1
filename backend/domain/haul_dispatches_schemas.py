from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints


def blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


OptionalCode = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)] | None,
    BeforeValidator(blank_to_none),
]


class PlanDispatch(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    # Optional only for callers that ask the workbench to resolve the current
    # truck/route/cycle advisory.  Existing clients may continue to pass it.
    advisory: OptionalCode = None
    lot: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    truck: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    route: OptionalCode = None
    cycle: OptionalCode = None


class SignReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dispatch: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    receipt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

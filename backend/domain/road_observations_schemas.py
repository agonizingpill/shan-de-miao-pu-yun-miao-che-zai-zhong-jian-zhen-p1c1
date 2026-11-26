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


class RecordRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    route: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    rack_type: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    load_kg: FiniteFloat
    rms: FiniteFloat
    sensor_ref: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class VerifyRun(BaseModel):
    # Allow workbench checkbox spellings such as holdout/as_holdout/selected.
    model_config = ConfigDict(extra="allow")
    observation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    holdout: bool | None = None
    is_holdout: bool | None = None
    as_holdout: bool | None = None
    selected: bool | None = None
    holdout_selected: bool | None = None
    holdout_batch: OptionalCode = None


class SelectHoldout(BaseModel):
    model_config = ConfigDict(extra="allow")
    observation: OptionalCode = None
    code: OptionalCode = None
    codes: Any = None
    observations: Any = None
    holdout_codes: Any = None
    batch: OptionalCode = None
    holdout_batch: OptionalCode = None

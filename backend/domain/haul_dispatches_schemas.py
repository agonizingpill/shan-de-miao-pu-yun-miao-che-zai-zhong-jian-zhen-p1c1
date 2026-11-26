from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class PlanDispatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    advisory: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    lot: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    truck: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class SignReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dispatch: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    receipt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

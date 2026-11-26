from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class SignStrap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truck: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    rack_type: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    strap_mark: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    cycle: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class WithdrawStrap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truck: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    strap_mark: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class FitLoad(BaseModel):
    model_config = ConfigDict(extra="forbid")
    truck: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    route: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    cycle: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    rms_goal: FiniteFloat


class ConfirmLoad(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    token: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

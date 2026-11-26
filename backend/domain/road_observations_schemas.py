from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class RecordRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    route: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    rack_type: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    load_kg: FiniteFloat
    rms: FiniteFloat
    sensor_ref: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class VerifyRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]

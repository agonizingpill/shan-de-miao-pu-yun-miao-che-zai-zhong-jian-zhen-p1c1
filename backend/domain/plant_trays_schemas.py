from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class MeasureTrays(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    plants: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    rack_type: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    trays: int
    tare_kg: FiniteFloat
    stock_kg: FiniteFloat

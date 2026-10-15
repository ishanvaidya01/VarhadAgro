from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

class CropDataRow(BaseModel):
    crop: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2100)
    yield_t_ha: float = Field(..., ge=0.0)
    t2m_avg: float = Field(...)
    precip_mm: float = Field(..., ge=0.0)
    extreme_heat_days: int = Field(..., ge=0)
    data_source: str = Field(...)

def validate_dataframe(df):
    valid_rows = []
    errors = []
    
    for i, row in df.iterrows():
        try:
            validated = CropDataRow(**row.to_dict())
            valid_rows.append(validated.model_dump())
        except ValidationError as e:
            errors.append({"row": i, "errors": str(e)})
            
    return valid_rows, errors

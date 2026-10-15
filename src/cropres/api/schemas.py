from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ScenarioRequest(BaseModel):
    district: str = Field(..., description="1966 Parent district name (e.g. Akola, Nagpur)")
    crop: str = Field(..., description="Crop name (e.g. Cotton, Soybean, Wheat)")
    temp_shift: float = Field(0.0, ge=-5.0, le=10.0, description="Temperature shift delta in degrees C")
    precip_shift: float = Field(0.0, ge=-0.80, le=2.0, description="Fractional precipitation change (-0.20 for -20%)")
    heat_days_shift: int = Field(0, ge=0, le=60, description="Additional extreme heat days (Tmax >= 38 C)")
    history_years: int = Field(30, ge=10, le=40, description="Number of historical daily weather years to simulate")

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str) -> str:
        s = v.strip().title()
        valid = {"Akola", "Amravati", "Buldhana", "Yavatmal", "Wardha", "Nagpur", "Bhandara", "Chandrapur"}
        if s not in valid:
            raise ValueError(f"Unknown district '{v}'. Valid Vidarbha parent districts: {sorted(list(valid))}")
        return s

    @field_validator("crop")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        s = v.strip().title()
        valid = {"Cotton", "Soybean", "Pigeonpea", "Sorghum", "Rice", "Wheat", "Chickpea"}
        if s not in valid:
            raise ValueError(f"Unknown crop '{v}'. Supported crops: {sorted(list(valid))}")
        return s


class AnalogRequest(BaseModel):
    district: str = Field(..., description="Target district name")
    temp_shift: float = Field(0.0, ge=-5.0, le=10.0, description="Temperature shift delta in degrees C")
    precip_shift: float = Field(0.0, ge=-0.80, le=2.0, description="Fractional precipitation change")
    heat_days_shift: int = Field(0, ge=0, le=60, description="Additional extreme heat days")
    top_k: int = Field(4, ge=1, le=10, description="Number of nearest analog districts to return")

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str) -> str:
        s = v.strip().title()
        valid = {"Akola", "Amravati", "Buldhana", "Yavatmal", "Wardha", "Nagpur", "Bhandara", "Chandrapur"}
        if s not in valid:
            raise ValueError(f"Unknown district '{v}'. Valid districts: {sorted(list(valid))}")
        return s

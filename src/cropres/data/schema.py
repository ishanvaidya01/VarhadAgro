from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd
import numpy as np

# Plausible yield bounds (in kg/ha) based on historical Maharashtra/Vidarbha agronomic data
YIELD_BOUNDS_KG_HA = {
    "Cotton": (20.0, 2500.0),
    "Soybean": (50.0, 4000.0),
    "Pigeonpea": (50.0, 3000.0),
    "Sorghum": (50.0, 3500.0),
    "Rice": (100.0, 5000.0),
    "Wheat": (100.0, 4500.0),
    "Chickpea": (50.0, 3000.0),
}

VALID_DISTRICTS = {
    "Akola", "Amravati", "Bhandara", "Buldhana",
    "Chandrapur", "Nagpur", "Wardha", "Yavatmal"
}

VALID_CROPS = set(YIELD_BOUNDS_KG_HA.keys())


class DistrictYieldRecord(BaseModel):
    district: str
    year: int = Field(ge=1950, le=2030)
    crop: str
    season: str
    area_1000ha: Optional[float] = Field(default=None, ge=0.0)
    production_1000t: Optional[float] = Field(default=None, ge=0.0)
    yield_kg_ha: Optional[float] = Field(default=None, ge=0.0)
    data_source: str = "ICRISAT_DLD"

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str) -> str:
        if v not in VALID_DISTRICTS:
            raise ValueError(f"Unknown district '{v}'. Must be one of {sorted(VALID_DISTRICTS)}")
        return v

    @field_validator("crop")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        if v not in VALID_CROPS:
            raise ValueError(f"Unsupported crop '{v}'. Must be one of {sorted(VALID_CROPS)}")
        return v


class DailyWeatherRecord(BaseModel):
    district: str
    date: str
    year: int = Field(ge=1970, le=2030)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    day_of_year: int = Field(ge=1, le=366)
    t2m: Optional[float] = Field(default=None, ge=-10.0, le=60.0)
    t2m_max: Optional[float] = Field(default=None, ge=-5.0, le=60.0)
    t2m_min: Optional[float] = Field(default=None, ge=-15.0, le=45.0)
    precip_mm: Optional[float] = Field(default=None, ge=0.0, le=1000.0)
    gwetroot: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sfc_sw_dwn: Optional[float] = Field(default=None, ge=0.0, le=50.0)
    data_source: str = "NASA_POWER"

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str) -> str:
        if v not in VALID_DISTRICTS:
            raise ValueError(f"Unknown district '{v}' in weather record.")
        return v


def validate_yield_panel(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates a yield panel DataFrame.
    Checks:
    - Pydantic schema conformance
    - Plausible yield ranges per crop
    - Year continuity per district-crop
    - Outlier identification (IQR based, flagged rather than auto-deleted)
    """
    valid_rows = []
    errors = []
    outlier_flags = []
    
    for idx, row in df.iterrows():
        try:
            record = DistrictYieldRecord(
                district=str(row["district"]),
                year=int(row["year"]),
                crop=str(row["crop"]),
                season=str(row.get("season", "Kharif")),
                area_1000ha=float(row["area_1000ha"]) if pd.notna(row.get("area_1000ha")) else None,
                production_1000t=float(row["production_1000t"]) if pd.notna(row.get("production_1000t")) else None,
                yield_kg_ha=float(row["yield_kg_ha"]) if pd.notna(row.get("yield_kg_ha")) else None,
                data_source=str(row.get("data_source", "ICRISAT_DLD")),
            )
            valid_rows.append(record.model_dump())
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})

    clean_df = pd.DataFrame(valid_rows)
    
    # Check plausible yield bounds
    plausibility_flags = []
    for crop, bounds in YIELD_BOUNDS_KG_HA.items():
        low, high = bounds
        crop_mask = (clean_df["crop"] == crop) & (clean_df["yield_kg_ha"].notna())
        implausible = clean_df[crop_mask & ((clean_df["yield_kg_ha"] < low) | (clean_df["yield_kg_ha"] > high))]
        for _, imp_row in implausible.iterrows():
            plausibility_flags.append({
                "district": imp_row["district"],
                "crop": imp_row["crop"],
                "year": imp_row["year"],
                "yield_kg_ha": imp_row["yield_kg_ha"],
                "bounds": bounds,
                "reason": "outside_agronomic_plausibility_bounds"
            })
            
    # Check year continuity
    continuity_report = {}
    for (dist, crop), group in clean_df.groupby(["district", "crop"]):
        valid_years = group[group["yield_kg_ha"].notna()]["year"].sort_values().tolist()
        if len(valid_years) > 1:
            diffs = np.diff(valid_years)
            gaps = [int(valid_years[i]) for i, d in enumerate(diffs) if d > 1]
            continuity_report[f"{dist}_{crop}"] = {
                "total_years": len(valid_years),
                "min_year": int(min(valid_years)),
                "max_year": int(max(valid_years)),
                "has_gaps": len(gaps) > 0,
                "gap_after_years": gaps
            }

    # Outlier detection via rolling 10-year IQR
    clean_df["is_outlier"] = False
    for (dist, crop), group in clean_df.groupby(["district", "crop"]):
        y_series = group.dropna(subset=["yield_kg_ha"]).copy()
        if len(y_series) >= 10:
            q25 = y_series["yield_kg_ha"].quantile(0.25)
            q75 = y_series["yield_kg_ha"].quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - 2.5 * iqr
            upper_bound = q75 + 2.5 * iqr
            outlier_indices = y_series[
                (y_series["yield_kg_ha"] < lower_bound) | (y_series["yield_kg_ha"] > upper_bound)
            ].index
            clean_df.loc[outlier_indices, "is_outlier"] = True

    validation_summary = {
        "total_records": len(df),
        "valid_records": len(clean_df),
        "validation_errors": errors,
        "implausible_yield_flags": plausibility_flags,
        "continuity": continuity_report,
        "outlier_count": int(clean_df["is_outlier"].sum())
    }
    
    return clean_df, validation_summary

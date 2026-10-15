"""
Generate a lightweight synthetic weather_daily_vidarbha.parquet for CI testing.

This script creates climatologically plausible daily weather records for all
8 Vidarbha districts (1981-2023) that match the schema consumed by:
  - cropres.api.service.ArtifactService
  - cropres.scenario.perturbation.ScenarioEngine
  - cropres.features.builder.build_feature_table

Columns: date, district, year, month, day, day_of_year,
         t2m, t2m_max, t2m_min, precip_mm, gwetroot, sfc_sw_dwn

Usage:
    python scripts/generate_test_weather.py
"""

import os
import numpy as np
import pandas as pd

DISTRICTS = [
    "Akola", "Amravati", "Bhandara", "Buldhana",
    "Chandrapur", "Nagpur", "Wardha", "Yavatmal",
]

# Climatological baselines per district (approximate Vidarbha normals)
# Keys: mean_tmax_jun_oct, mean_tmin_jun_oct, season_rain_mm, annual_solar
CLIM = {
    "Akola":     {"tmax": 33.5, "tmin": 23.5, "rain": 745,  "solar": 20.0},
    "Amravati":  {"tmax": 32.8, "tmin": 23.0, "rain": 810,  "solar": 19.5},
    "Bhandara":  {"tmax": 32.5, "tmin": 22.5, "rain": 1250, "solar": 18.5},
    "Buldhana":  {"tmax": 33.1, "tmin": 23.2, "rain": 680,  "solar": 20.5},
    "Chandrapur":{"tmax": 33.8, "tmin": 23.8, "rain": 1180, "solar": 19.0},
    "Nagpur":    {"tmax": 32.7, "tmin": 22.8, "rain": 985,  "solar": 19.5},
    "Wardha":    {"tmax": 33.0, "tmin": 23.0, "rain": 930,  "solar": 19.8},
    "Yavatmal":  {"tmax": 33.2, "tmin": 23.5, "rain": 890,  "solar": 19.5},
}

START_YEAR = 1981
END_YEAR = 2023


def generate_district_weather(district: str, rng: np.random.Generator) -> pd.DataFrame:
    """Generate daily weather for one district across all years."""
    c = CLIM[district]
    rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        n = len(dates)
        months = dates.month.values
        days = dates.day.values
        doys = dates.dayofyear.values

        # Seasonal temperature cycle: peaks in May (month 5), coolest in Jan
        # Using a sinusoidal model anchored to month
        month_frac = (months - 1) / 11.0  # 0 to 1
        # Peak around May (index ~4), trough around Dec-Jan
        seasonal_t = np.sin(np.pi * (month_frac - 0.08))  # peaks ~May
        # Scale: winter ~20C tmax, summer ~42C tmax
        tmax_base = c["tmax"] + seasonal_t * 5.0
        tmax = tmax_base + rng.normal(0, 1.5, n)
        tmin_base = c["tmin"] + seasonal_t * 3.0
        tmin = tmin_base + rng.normal(0, 1.2, n)
        # Ensure tmin < tmax
        tmin = np.minimum(tmin, tmax - 2.0)
        t2m = (tmax + tmin) / 2.0

        # Monsoon rainfall (June-September dominant)
        # Daily rainfall from a zero-inflated gamma distribution
        is_monsoon = np.isin(months, [6, 7, 8, 9])
        rain_prob_monsoon = 0.55  # ~55% of monsoon days have rain
        rain_prob_dry = 0.05     # ~5% outside monsoon

        rain_flag = np.where(
            is_monsoon,
            rng.random(n) < rain_prob_monsoon,
            rng.random(n) < rain_prob_dry
        )
        # Gamma shape~0.8, scale adjusted to match total season rainfall
        # Target total: ~c["rain"] mm across JJAS (~122 days)
        monsoon_days = np.sum(is_monsoon)
        target_mean_rainy_day = c["rain"] / (monsoon_days * rain_prob_monsoon)
        gamma_shape = 0.8
        gamma_scale = target_mean_rainy_day / gamma_shape

        precip = np.where(
            rain_flag,
            rng.gamma(gamma_shape, gamma_scale, n),
            0.0
        )
        precip = np.maximum(0.0, precip)

        # Root zone soil wetness: higher during monsoon, lower in dry season
        gwet_base = np.where(is_monsoon, 0.65, 0.30)
        gwetroot = gwet_base + rng.normal(0, 0.08, n)
        gwetroot = np.clip(gwetroot, 0.05, 0.95)

        # Shortwave solar radiation (MJ/m^2/day)
        # Lower during cloudy monsoon, higher in clear dry season
        sw_base = np.where(is_monsoon, c["solar"] - 4.0, c["solar"] + 2.0)
        sfc_sw_dwn = sw_base + rng.normal(0, 2.0, n)
        sfc_sw_dwn = np.maximum(2.0, sfc_sw_dwn)

        date_strs = dates.strftime("%Y-%m-%d").tolist()

        for i in range(n):
            rows.append({
                "date": date_strs[i],
                "district": district,
                "year": int(year),
                "month": int(months[i]),
                "day": int(days[i]),
                "day_of_year": int(doys[i]),
                "t2m": round(float(t2m[i]), 2),
                "t2m_max": round(float(tmax[i]), 2),
                "t2m_min": round(float(tmin[i]), 2),
                "precip_mm": round(float(precip[i]), 2),
                "gwetroot": round(float(gwetroot[i]), 3),
                "sfc_sw_dwn": round(float(sfc_sw_dwn[i]), 2),
            })

    return pd.DataFrame(rows)


def main():
    output_path = os.path.join("data", "raw", "weather_daily_vidarbha.parquet")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rng = np.random.default_rng(seed=42)

    frames = []
    for dist in DISTRICTS:
        print(f"  Generating weather for {dist}...")
        df = generate_district_weather(dist, rng)
        frames.append(df)

    full_df = pd.concat(frames, ignore_index=True)
    full_df.to_parquet(output_path, index=False)
    print(f"Wrote {len(full_df)} rows to {output_path}")


if __name__ == "__main__":
    main()

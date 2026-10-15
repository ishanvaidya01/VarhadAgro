import os
import json
import hashlib
import time
import requests
import pandas as pd
from datetime import datetime, timezone

# Vidarbha district centroids (1966 parent districts)
DISTRICT_CENTROIDS = {
    "Akola": {"lat": 20.70, "lon": 77.01, "notes": "Akola and Washim"},
    "Amravati": {"lat": 20.93, "lon": 77.75, "notes": "Amravati"},
    "Bhandara": {"lat": 21.17, "lon": 79.65, "notes": "Bhandara and Gondia"},
    "Buldhana": {"lat": 20.53, "lon": 76.18, "notes": "Buldhana"},
    "Chandrapur": {"lat": 19.96, "lon": 79.30, "notes": "Chandrapur and Gadchiroli"},
    "Nagpur": {"lat": 21.15, "lon": 79.08, "notes": "Nagpur"},
    "Wardha": {"lat": 20.74, "lon": 78.60, "notes": "Wardha"},
    "Yavatmal": {"lat": 20.39, "lon": 78.13, "notes": "Yavatmal (Yeotmal)"}
}

START_DATE = "19810101"
END_DATE = "20231231"
PARAMETERS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,GWETROOT,ALLSKY_SFC_SW_DWN"
COMMUNITY = "AG"
LICENSE = "NASA Open Data Policy (Public Domain / US Government Open Data)"

def update_provenance(record_key, info):
    prov_file = "data/provenance.json"
    os.makedirs(os.path.dirname(prov_file), exist_ok=True)
    prov = {}
    if os.path.exists(prov_file):
        try:
            with open(prov_file, "r") as f:
                prov = json.load(f)
        except Exception:
            prov = {}
    prov[record_key] = info
    with open(prov_file, "w") as f:
        json.dump(prov, f, indent=2)

def fetch_district_weather(district, lat, lon):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters={PARAMETERS}&community={COMMUNITY}&longitude={lon}&latitude={lat}&"
        f"start={START_DATE}&end={END_DATE}&format=JSON"
    )
    print(f"Fetching weather for {district} ({lat}, {lon})...")
    resp = requests.get(url, timeout=90)
    resp.raise_for_status()
    data = resp.json()
    params = data["properties"]["parameter"]
    
    # Dates are common across variables
    dates = sorted(params["T2M"].keys())
    records = []
    for d_str in dates:
        dt = datetime.strptime(d_str, "%Y%m%d")
        
        # NASA POWER missing value sentinel is -999.0
        def clean_val(v):
            return None if v is None or v <= -900 else float(v)
            
        records.append({
            "district": district,
            "date": dt.strftime("%Y-%m-%d"),
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "day_of_year": dt.timetuple().tm_yday,
            "t2m": clean_val(params["T2M"].get(d_str)),
            "t2m_max": clean_val(params["T2M_MAX"].get(d_str)),
            "t2m_min": clean_val(params["T2M_MIN"].get(d_str)),
            "precip_mm": clean_val(params["PRECTOTCORR"].get(d_str)),
            "gwetroot": clean_val(params.get("GWETROOT", {}).get(d_str)),
            "sfc_sw_dwn": clean_val(params.get("ALLSKY_SFC_SW_DWN", {}).get(d_str)),
            "data_source": "NASA_POWER"
        })
    return records

def download_all_weather():
    os.makedirs("data/raw", exist_ok=True)
    all_records = []
    
    for district, coords in DISTRICT_CENTROIDS.items():
        t0 = time.time()
        rec = fetch_district_weather(district, coords["lat"], coords["lon"])
        dt = time.time() - t0
        print(f"  -> {district}: {len(rec)} days fetched in {dt:.1f}s")
        all_records.extend(rec)
        # Small delay to be respectful of NASA POWER rate limit
        time.sleep(1.0)
        
    df = pd.DataFrame(all_records)
    print(f"\nTotal daily weather records: {len(df)}")
    
    parquet_path = "data/raw/weather_daily_vidarbha.parquet"
    csv_path = "data/raw/weather_daily_vidarbha.csv.gz"
    
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False, compression="gzip")
    print(f"Saved weather data to {parquet_path} and {csv_path}")
    
    # Calculate sha256 of parquet
    with open(parquet_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
        
    update_provenance("nasa_power_weather", {
        "source_name": "NASA POWER Daily Agroclimatology (Point API)",
        "provider": "NASA Langley Research Center POWER Project",
        "parameters": PARAMETERS.split(","),
        "community": COMMUNITY,
        "license": LICENSE,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "sha256_parquet": sha256,
        "date_range": [START_DATE, END_DATE],
        "districts": list(DISTRICT_CENTROIDS.keys()),
        "output_files": [parquet_path, csv_path]
    })
    print("Weather provenance logged successfully.")
    return df

if __name__ == "__main__":
    download_all_weather()

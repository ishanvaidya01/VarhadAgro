import os
import io
import json
import hashlib
import zipfile
import requests
import pandas as pd
from datetime import datetime, timezone

ICRISAT_URL = "https://raw.githubusercontent.com/swapnilprasad69/Indian-Agriculture-Data-Analysis/main/ICRISAT-District%20Level%20Data.csv.zip"
DOI = "10.21421/D2/XFB1BZ"
LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"

DISTRICT_MAPPING = {
    "Akola": "Akola",
    "Amarawati": "Amravati",
    "Bhandara": "Bhandara",
    "Buldhana": "Buldhana",
    "Chandrapur": "Chandrapur",
    "Nagpur": "Nagpur",
    "Wardha": "Wardha",
    "Yeotmal": "Yavatmal"
}

CROPS = {
    "Cotton": {
        "area_col": "COTTON AREA (1000 ha)",
        "prod_col": "COTTON PRODUCTION (1000 tons)",
        "yield_col": "COTTON YIELD (Kg per ha)",
        "season": "Kharif"
    },
    "Soybean": {
        "area_col": "SOYABEAN AREA (1000 ha)",
        "prod_col": "SOYABEAN PRODUCTION (1000 tons)",
        "yield_col": "SOYABEAN YIELD (Kg per ha)",
        "season": "Kharif"
    },
    "Pigeonpea": {
        "area_col": "PIGEONPEA AREA (1000 ha)",
        "prod_col": "PIGEONPEA PRODUCTION (1000 tons)",
        "yield_col": "PIGEONPEA YIELD (Kg per ha)",
        "season": "Kharif"
    },
    "Sorghum": {
        "area_col": "SORGHUM AREA (1000 ha)",
        "prod_col": "SORGHUM PRODUCTION (1000 tons)",
        "yield_col": "SORGHUM YIELD (Kg per ha)",
        "season": "Kharif/Rabi"
    },
    "Rice": {
        "area_col": "RICE AREA (1000 ha)",
        "prod_col": "RICE PRODUCTION (1000 tons)",
        "yield_col": "RICE YIELD (Kg per ha)",
        "season": "Kharif"
    },
    "Wheat": {
        "area_col": "WHEAT AREA (1000 ha)",
        "prod_col": "WHEAT PRODUCTION (1000 tons)",
        "yield_col": "WHEAT YIELD (Kg per ha)",
        "season": "Rabi"
    },
    "Chickpea": {
        "area_col": "CHICKPEA AREA (1000 ha)",
        "prod_col": "CHICKPEA PRODUCTION (1000 tons)",
        "yield_col": "CHICKPEA YIELD (Kg per ha)",
        "season": "Rabi"
    }
}

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

def download_and_process_yield():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/interim", exist_ok=True)
    
    print(f"Fetching ICRISAT DLD dataset from: {ICRISAT_URL}")
    resp = requests.get(ICRISAT_URL, timeout=60)
    resp.raise_for_status()
    raw_bytes = resp.content
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
        filename = z.namelist()[0]
        with z.open(filename) as f:
            full_df = pd.read_csv(f)
            
    print(f"Total ICRISAT records: {len(full_df)}")
    
    # Filter for Maharashtra and Vidarbha 1966 districts
    mh_df = full_df[full_df["State Name"].str.upper() == "MAHARASHTRA"].copy()
    
    # Save raw Maharashtra data for analog candidate pool
    mh_raw_path = "data/raw/icrisat_dld_maharashtra.csv"
    mh_df.to_csv(mh_raw_path, index=False)
    
    vidarbha_raw = mh_df[mh_df["Dist Name"].isin(DISTRICT_MAPPING.keys())].copy()
    vidarbha_raw["district"] = vidarbha_raw["Dist Name"].map(DISTRICT_MAPPING)
    v_raw_path = "data/raw/icrisat_dld_vidarbha_raw.csv"
    vidarbha_raw.to_csv(v_raw_path, index=False)
    
    # Reshape into tidy panel: district, year, crop, season, area_1000ha, prod_1000t, yield_kg_ha
    records = []
    for _, row in vidarbha_raw.iterrows():
        dist = row["district"]
        year = int(row["Year"])
        for crop_name, info in CROPS.items():
            area = row.get(info["area_col"], None)
            prod = row.get(info["prod_col"], None)
            yld = row.get(info["yield_col"], None)
            
            # Treat negative or missing as NaN
            area_val = float(area) if pd.notna(area) and float(area) >= 0 else None
            prod_val = float(prod) if pd.notna(prod) and float(prod) >= 0 else None
            yld_val = float(yld) if pd.notna(yld) and float(yld) >= 0 else None
            
            # If yield is missing but area and prod exist, calculate: (prod * 1000 * 1000) / (area * 1000) = prod * 1000 / area
            if yld_val is None and area_val and prod_val and area_val > 0:
                yld_val = round((prod_val * 1000.0) / area_val, 2)
                
            records.append({
                "district": dist,
                "year": year,
                "crop": crop_name,
                "season": info["season"],
                "area_1000ha": area_val,
                "production_1000t": prod_val,
                "yield_kg_ha": yld_val,
                "data_source": "ICRISAT_DLD"
            })
            
    tidy_df = pd.DataFrame(records)
    interim_path = "data/interim/vidarbha_yield_panel.csv"
    tidy_df.to_csv(interim_path, index=False)
    print(f"Generated clean yield panel: {len(tidy_df)} rows saved to {interim_path}")
    
    # Record provenance
    update_provenance("icrisat_dld_yield", {
        "source_name": "ICRISAT District Level Database (DLD) for Indian Agriculture",
        "doi": DOI,
        "url": ICRISAT_URL,
        "license": LICENSE,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256,
        "years_covered": [int(tidy_df["year"].min()), int(tidy_df["year"].max())],
        "spatial_units": "1966 District Boundaries (8 parent districts covering 11 modern Vidarbha districts)",
        "crops": list(CROPS.keys()),
        "output_files": [mh_raw_path, v_raw_path, interim_path]
    })
    print("Yield provenance logged successfully.")
    return tidy_df

if __name__ == "__main__":
    download_and_process_yield()

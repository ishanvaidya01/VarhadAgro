import pandas as pd
import numpy as np
import os
import sqlite3

def generate_synthetic_data(output_path="data/raw/synthetic_data.csv", metadata_db="data/processed/metadata.db"):
    # Fix random seed for reproducibility
    np.random.seed(42)
    
    crops = ["Wheat", "Rice", "Maize", "Soybean", "Sorghum"]
    regions = [f"Region_{i}" for i in range(1, 11)]
    years = list(range(1994, 2024)) # 30 years
    
    data = []
    
    for crop in crops:
        for region in regions:
            # Base yield differs by region and crop
            base_yield = np.random.uniform(1.5, 4.5)
            # Technology trend (annual increase)
            trend = np.random.uniform(0.01, 0.03)
            
            for year in years:
                # Weather variables
                t2m = np.random.normal(25, 2)
                precip = np.random.lognormal(mean=5.0, sigma=0.5)
                extreme_heat_days = int(np.random.poisson(lam=max(0, (t2m - 24) * 2)))
                
                # Yield calculation with climate effects and noise
                # Negative impact from extreme heat, positive from precipitation up to a point
                climate_effect = (precip * 0.001) - (extreme_heat_days * 0.05)
                noise = np.random.normal(0, 0.2)
                
                current_yield = base_yield + (year - 1994) * trend + climate_effect + noise
                current_yield = max(0.1, current_yield) # Ensure positive yield
                
                data.append({
                    "crop": crop,
                    "region": region,
                    "year": year,
                    "yield_t_ha": round(current_yield, 3),
                    "t2m_avg": round(t2m, 2),
                    "precip_mm": round(precip, 1),
                    "extreme_heat_days": extreme_heat_days,
                    "data_source": "synthetic_demo"
                })
                
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    # Record provenance
    os.makedirs(os.path.dirname(metadata_db), exist_ok=True)
    conn = sqlite3.connect(metadata_db)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS provenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            retrieval_date TEXT,
            parameters TEXT,
            checksum TEXT,
            data_source TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO provenance (source_url, retrieval_date, parameters, checksum, data_source)
        VALUES (?, datetime('now'), ?, ?, ?)
    ''', ("local_synthetic_generator", '{"crops": 5, "regions": 10, "years": 30}', "static_checksum", "synthetic_demo"))
    conn.commit()
    conn.close()
    
    print(f"Generated synthetic data: {df.shape[0]} rows saved to {output_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_data()

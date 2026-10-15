import requests
import zipfile
import io
import pandas as pd

def inspect():
    url = 'https://raw.githubusercontent.com/swapnilprasad69/Indian-Agriculture-Data-Analysis/main/ICRISAT-District%20Level%20Data.csv.zip'
    print("Downloading ICRISAT zip...")
    r = requests.get(url, timeout=30)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        with z.open(z.namelist()[0]) as f:
            df = pd.read_csv(f)

    mh = df[df['State Name'].str.upper() == 'MAHARASHTRA'].copy()
    vidarbha_districts = ['Akola', 'Amarawati', 'Bhandara', 'Buldhana', 'Chandrapur', 'Nagpur', 'Wardha', 'Yeotmal']
    vdf = mh[mh['Dist Name'].isin(vidarbha_districts)].copy()
    print(f"Vidarbha rows: {len(vdf)}, districts: {vdf['Dist Name'].nunique()}, years: {vdf['Year'].min()} to {vdf['Year'].max()}")

    candidate_crops = {
        'Cotton': ('COTTON AREA (1000 ha)', 'COTTON YIELD (Kg per ha)'),
        'Soybean': ('SOYABEAN AREA (1000 ha)', 'SOYABEAN YIELD (Kg per ha)'),
        'Pigeonpea': ('PIGEONPEA AREA (1000 ha)', 'PIGEONPEA YIELD (Kg per ha)'),
        'Sorghum': ('SORGHUM AREA (1000 ha)', 'SORGHUM YIELD (Kg per ha)'),
        'Rice': ('RICE AREA (1000 ha)', 'RICE YIELD (Kg per ha)'),
        'Wheat': ('WHEAT AREA (1000 ha)', 'WHEAT YIELD (Kg per ha)'),
        'Chickpea': ('CHICKPEA AREA (1000 ha)', 'CHICKPEA YIELD (Kg per ha)')
    }

    table = []
    for crop, (area_col, yield_col) in candidate_crops.items():
        for dist in sorted(vidarbha_districts):
            sub = vdf[vdf['Dist Name'] == dist]
            valid = sub[(sub[yield_col].notna()) & (sub[yield_col] > 0)]
            mean_area = sub[area_col].mean()
            table.append({
                'District': dist,
                'Crop': crop,
                'Total_Years': len(valid),
                'Min_Year': int(valid['Year'].min()) if len(valid) else None,
                'Max_Year': int(valid['Year'].max()) if len(valid) else None,
                'Mean_Area_1000ha': round(float(mean_area), 2) if pd.notna(mean_area) else 0.0,
                'Mean_Yield_kg_ha': round(float(valid[yield_col].mean()), 1) if len(valid) else 0.0
            })

    tdf = pd.DataFrame(table)
    print("\n--- Vidarbha Crop Coverage (ICRISAT DLD) ---")
    print(tdf.to_string())

    # Check criteria: >= 25 years and non-trivial area share
    valid_pairs = tdf[(tdf['Total_Years'] >= 25) & (tdf['Mean_Area_1000ha'] >= 2.0)]
    print("\n--- Pairs meeting criteria (>= 25 years & >= 2k ha) ---")
    print(valid_pairs[['District', 'Crop', 'Total_Years', 'Mean_Area_1000ha', 'Mean_Yield_kg_ha']].to_string())

if __name__ == "__main__":
    inspect()

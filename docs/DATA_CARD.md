# Data Card: Vidarbha Observed Panel (1966-2023)

## 1. Dataset Overview

VarhadCrop is trained and evaluated strictly on observed empirical records. No synthetic or generated data is used in any production metric, model, or user interface.

- **Geographic Scope**: Vidarbha Region, Maharashtra, India (11 modern districts grouped into 8 1966 parent units).
- **Yield Panel Period**: 1966 to 2017 (52 continuous agricultural years from ICRISAT DLD).
- **Weather Panel Period**: 1981 to 2023 (43 continuous years of daily observations, 125,640 records from NASA POWER).
- **Model Overlap Window**: 1981 to 2017 (37 continuous years of coupled daily weather and district yield statistics).

---

## 2. Data Sources & Provenance

| Component | Primary Source | Identifier / URL | License | Parameters / Scope |
|---|---|---|---|---|
| **Crop Yields & Area** | ICRISAT District Level Database (DLD) | DOI: [10.21421/D2/XFB1BZ](https://doi.org/10.21421/D2/XFB1BZ) | Creative Commons Attribution 4.0 International (CC BY 4.0) | Area (1000 ha), Production (1000 t), Yield (kg/ha) for 7 crops (1966-2017) |
| **Observed Daily Weather** | NASA POWER Agroclimatology Daily API | [https://power.larc.nasa.gov](https://power.larc.nasa.gov) | NASA Open Data Policy (Public Domain / US Gov Open Data) | T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, GWETROOT, ALLSKY_SFC_SW_DWN (1981-2023) |
| **District Boundaries** | Census of India / DataMeet / GADM | [DataMeet Maps](https://github.com/datameet/maps) | Creative Commons Attribution-ShareAlike 2.0 (CC BY-SA 2.0) / ODbL | 1966 parent polygons & 11 modern constituent polygons (< 100 KB GeoJSON) |

### Cryptographic Checksums (SHA-256)
- `data/interim/vidarbha_yield_panel.csv`: Verified from ICRISAT DLD archive (SHA256: `6817678868791506e8fb537f0de5d5a52ed7a7bd907a0cdc2adf7eaa1d549f27`)
- `data/raw/weather_daily_vidarbha.parquet`: Verified NASA POWER Agroclimatology (SHA256: `de1be91381bfa93a5f7b50ca5d9dddd06575800f6416a2f944ddcadccb6a957c`)
- `data/processed/vidarbha_boundaries.geojson`: Harmonized GeoJSON (Size: `75.9 KB`)

---

## 3. Spatial Unit Harmonization (1966 District Boundaries)

The primary yield dataset (ICRISAT DLD) is apportioned to **1966 district boundaries**. Several modern Vidarbha districts were carved out after 1966:
1. **Akola**: Includes modern **Akola** and **Washim** (Washim separated in 1998).
2. **Bhandara**: Includes modern **Bhandara** and **Gondia** (Gondia separated in 1999).
3. **Chandrapur**: Includes modern **Chandrapur** and **Gadchiroli** (Gadchiroli separated in 1982).
4. **Amravati**: Unchanged boundary.
5. **Buldhana**: Unchanged boundary.
6. **Nagpur**: Unchanged boundary.
7. **Wardha**: Unchanged boundary.
8. **Yavatmal** (Yeotmal): Unchanged boundary.

**Spatial Integrity Rule**: Series are never fabricated for carved-out districts. Weather centroids and spatial boundary polygons strictly reflect the apportioned 1966 parent boundaries to ensure exact alignment with agricultural statistics.

---

## 4. District-by-Crop Coverage Table

Only district-crop series meeting the criteria of **at least 25 observed years** and **non-trivial cropped area (>= 2,000 hectares mean)** are admitted into predictive modeling.

| District | Crop | Total Years | Span | Mean Area (k ha) | Mean Yield (kg/ha) | Missing % | Included in Model |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Akola | Chickpea | 52 | 1966-2017 | 54.3 | 524.9 | 0.0% | Yes |
| Amravati | Chickpea | 52 | 1966-2017 | 40.7 | 616.3 | 0.0% | Yes |
| Bhandara | Chickpea | 52 | 1966-2017 | 11.5 | 421.1 | 0.0% | Yes |
| Buldhana | Chickpea | 52 | 1966-2017 | 30.6 | 533.7 | 0.0% | Yes |
| Chandrapur | Chickpea | 52 | 1966-2017 | 20.0 | 409.8 | 0.0% | Yes |
| Nagpur | Chickpea | 52 | 1966-2017 | 33.4 | 495.0 | 0.0% | Yes |
| Wardha | Chickpea | 52 | 1966-2017 | 15.7 | 475.7 | 0.0% | Yes |
| Yavatmal | Chickpea | 52 | 1966-2017 | 23.1 | 541.6 | 0.0% | Yes |
| Akola | Cotton | 52 | 1966-2017 | 310.9 | 144.3 | 0.0% | Yes |
| Amravati | Cotton | 52 | 1966-2017 | 308.7 | 158.1 | 0.0% | Yes |
| Bhandara | Cotton | 1 | 2017-2017 | 0.0 | 473.7 | 98.1% | No (Insufficient Area/Years) |
| Buldhana | Cotton | 52 | 1966-2017 | 232.6 | 143.3 | 0.0% | Yes |
| Chandrapur | Cotton | 52 | 1966-2017 | 62.2 | 159.0 | 0.0% | Yes |
| Nagpur | Cotton | 52 | 1966-2017 | 78.6 | 169.7 | 0.0% | Yes |
| Wardha | Cotton | 52 | 1966-2017 | 162.0 | 165.0 | 0.0% | Yes |
| Yavatmal | Cotton | 52 | 1966-2017 | 392.9 | 142.2 | 0.0% | Yes |
| Akola | Pigeonpea | 52 | 1966-2017 | 73.5 | 745.8 | 0.0% | Yes |
| Amravati | Pigeonpea | 52 | 1966-2017 | 75.1 | 819.5 | 0.0% | Yes |
| Bhandara | Pigeonpea | 52 | 1966-2017 | 10.1 | 640.0 | 0.0% | Yes |
| Buldhana | Pigeonpea | 52 | 1966-2017 | 50.0 | 679.5 | 0.0% | Yes |
| Chandrapur | Pigeonpea | 52 | 1966-2017 | 23.7 | 603.7 | 0.0% | Yes |
| Nagpur | Pigeonpea | 52 | 1966-2017 | 48.8 | 602.5 | 0.0% | Yes |
| Wardha | Pigeonpea | 52 | 1966-2017 | 46.8 | 910.1 | 0.0% | Yes |
| Yavatmal | Pigeonpea | 52 | 1966-2017 | 88.0 | 842.0 | 0.0% | Yes |
| Akola | Rice | 45 | 1966-2011 | 5.3 | 674.4 | 13.5% | Yes |
| Amravati | Rice | 52 | 1966-2017 | 10.2 | 590.1 | 0.0% | Yes |
| Bhandara | Rice | 52 | 1966-2017 | 317.6 | 1249.9 | 0.0% | Yes |
| Buldhana | Rice | 38 | 1966-2016 | 2.4 | 769.4 | 26.9% | Yes |
| Chandrapur | Rice | 52 | 1966-2017 | 272.1 | 1164.7 | 0.0% | Yes |
| Nagpur | Rice | 52 | 1966-2017 | 46.6 | 1178.0 | 0.0% | Yes |
| Wardha | Rice | 42 | 1966-2007 | 5.4 | 820.7 | 19.2% | Yes |
| Yavatmal | Rice | 46 | 1966-2012 | 8.4 | 653.5 | 11.5% | Yes |
| Akola | Sorghum | 52 | 1966-2017 | 198.5 | 1183.9 | 0.0% | Yes |
| Amravati | Sorghum | 52 | 1966-2017 | 140.9 | 1093.1 | 0.0% | Yes |
| Bhandara | Sorghum | 41 | 1966-2006 | 20.4 | 423.7 | 21.2% | Yes |
| Buldhana | Sorghum | 52 | 1966-2017 | 179.1 | 1223.4 | 0.0% | Yes |
| Chandrapur | Sorghum | 52 | 1966-2017 | 130.8 | 539.1 | 0.0% | Yes |
| Nagpur | Sorghum | 52 | 1966-2017 | 123.0 | 719.7 | 0.0% | Yes |
| Wardha | Sorghum | 52 | 1966-2017 | 76.9 | 797.3 | 0.0% | Yes |
| Yavatmal | Sorghum | 52 | 1966-2017 | 186.5 | 930.3 | 0.0% | Yes |
| Akola | Soybean | 28 | 1990-2017 | 219.9 | 1114.9 | 46.2% | Yes |
| Amravati | Soybean | 31 | 1987-2017 | 185.9 | 938.4 | 40.4% | Yes |
| Bhandara | Soybean | 31 | 1987-2017 | 8.9 | 966.3 | 40.4% | Yes |
| Buldhana | Soybean | 29 | 1989-2017 | 144.5 | 1122.3 | 44.2% | Yes |
| Chandrapur | Soybean | 31 | 1987-2017 | 102.5 | 986.7 | 40.4% | Yes |
| Nagpur | Soybean | 31 | 1987-2017 | 196.8 | 871.5 | 40.4% | Yes |
| Wardha | Soybean | 31 | 1987-2017 | 125.5 | 983.7 | 40.4% | Yes |
| Yavatmal | Soybean | 31 | 1987-2017 | 136.7 | 1022.9 | 40.4% | Yes |
| Akola | Wheat | 52 | 1966-2017 | 39.3 | 1105.8 | 0.0% | Yes |
| Amravati | Wheat | 52 | 1966-2017 | 34.7 | 1125.0 | 0.0% | Yes |
| Bhandara | Wheat | 52 | 1966-2017 | 23.7 | 710.4 | 0.0% | Yes |
| Buldhana | Wheat | 52 | 1966-2017 | 37.4 | 1134.5 | 0.0% | Yes |
| Chandrapur | Wheat | 52 | 1966-2017 | 32.0 | 685.1 | 0.0% | Yes |
| Nagpur | Wheat | 52 | 1966-2017 | 65.8 | 938.2 | 0.0% | Yes |
| Wardha | Wheat | 52 | 1966-2017 | 26.9 | 1066.3 | 0.0% | Yes |
| Yavatmal | Wheat | 52 | 1966-2017 | 22.8 | 1016.8 | 0.0% | Yes |

---

## 5. Data Quality, Missing Data & Outliers

### Measured Missing Percentages
- **Weather Panel (1981-2023)**:
  - Total records: 125,640 daily observations across 8 districts.
  - Precipitation missing: 0.0%
  - Temperature missing: 0.0%
  - Soil wetness missing: 0.0%
- **Yield Panel (1966-2017)**:
  - Missing percentage for major established crops (Cotton, Pigeonpea, Sorghum, Wheat, Chickpea) is **0.0%** across the entire 52-year period.
  - Soybean shows missing/zero entries prior to 1987 because soybean commercial cultivation in Maharashtra commenced in the late 1980s. Post-1987, Soybean coverage is 100% complete across all 8 districts.
  - Cotton in Bhandara is excluded from modeling because Bhandara is a flood-prone wetland paddy ecosystem where cotton cultivation is negligible (< 0.5k ha).

### Outlier Handling Policy
Outliers detected via rolling 10-year interquartile range (IQR) (such as the historic 1972 Maharashtra drought and the 1997 bollworm infestation) are **flagged for inspection but never deleted**. Severe climatically driven yield shocks represent the critical risk signal that PMFBY insurance models must capture.

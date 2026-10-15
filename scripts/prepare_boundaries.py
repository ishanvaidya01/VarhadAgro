import os
import json
import hashlib
import requests
from datetime import datetime, timezone
import shapely.geometry
from shapely.ops import unary_union

INDIA_GEOJSON_URL = "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson"

# Mapping modern districts to 1966 parent districts
# Akola was partitioned into Akola and Washim (1998)
# Bhandara was partitioned into Bhandara and Gondiya (1999)
# Chandrapur was partitioned into Chandrapur and Garhchiroli (1982)
MODERN_TO_1966 = {
    "Akola": "Akola",
    "Washim": "Akola",
    "Amravati": "Amravati",
    "Bhandara": "Bhandara",
    "Gondiya": "Bhandara",
    "Buldana": "Buldhana",
    "Chandrapur": "Chandrapur",
    "Garhchiroli": "Chandrapur",
    "Nagpur": "Nagpur",
    "Wardha": "Wardha",
    "Yavatmal": "Yavatmal"
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

def prepare_boundaries():
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("frontend/public", exist_ok=True)
    
    print(f"Downloading India district GeoJSON from: {INDIA_GEOJSON_URL}")
    resp = requests.get(INDIA_GEOJSON_URL, timeout=60)
    resp.raise_for_status()
    raw_content = resp.content
    sha256 = hashlib.sha256(raw_content).hexdigest()
    
    data = json.loads(raw_content.decode("utf-8"))
    features = data.get("features", [])
    print(f"Total features in dataset: {len(features)}")
    
    # Filter Maharashtra Vidarbha districts
    vidarbha_modern_features = []
    for f in features:
        props = f.get("properties", {})
        state = props.get("NAME_1") or props.get("st_nm") or ""
        dist = props.get("NAME_2") or props.get("district") or props.get("dtname") or ""
        if dist in MODERN_TO_1966:
            # Standardize district name
            clean_name = "Buldhana" if dist == "Buldana" else "Gondia" if dist == "Gondiya" else "Gadchiroli" if dist == "Garhchiroli" else dist
            geom = shapely.geometry.shape(f["geometry"])
            # Simplify geometry (tolerance ~0.005 degrees ~= 500m precision)
            simplified_geom = geom.simplify(0.005, preserve_topology=True)
            
            vidarbha_modern_features.append({
                "type": "Feature",
                "properties": {
                    "district": clean_name,
                    "parent_1966": MODERN_TO_1966[dist],
                    "state": "Maharashtra"
                },
                "geometry": shapely.geometry.mapping(simplified_geom)
            })
            
    print(f"Found {len(vidarbha_modern_features)} modern Vidarbha districts.")
    
    # Save modern 11-district GeoJSON
    modern_geojson = {
        "type": "FeatureCollection",
        "features": vidarbha_modern_features
    }
    modern_path = "data/processed/vidarbha_boundaries_modern.geojson"
    with open(modern_path, "w", encoding="utf-8") as f:
        json.dump(modern_geojson, f)
    print(f"Saved modern boundaries to {modern_path} (Size: {os.path.getsize(modern_path) / 1024:.1f} KB)")
    
    # Dissolve to 1966 parent districts
    by_parent = {}
    for f in vidarbha_modern_features:
        parent = f["properties"]["parent_1966"]
        geom = shapely.geometry.shape(f["geometry"])
        if parent not in by_parent:
            by_parent[parent] = []
        by_parent[parent].append(geom)
        
    parent_1966_features = []
    for parent_name, geoms in sorted(by_parent.items()):
        if len(geoms) == 1:
            union_geom = geoms[0]
        else:
            union_geom = unary_union(geoms)
            
        simplified_union = union_geom.simplify(0.005, preserve_topology=True)
        # Compute centroid for reference
        c = simplified_union.centroid
        
        parent_1966_features.append({
            "type": "Feature",
            "properties": {
                "district": parent_name,
                "district_code": parent_name.upper(),
                "centroid_lon": round(c.x, 4),
                "centroid_lat": round(c.y, 4),
                "state": "Maharashtra",
                "notes": "1966 base boundary apportioned in ICRISAT DLD"
            },
            "geometry": shapely.geometry.mapping(simplified_union)
        })
        
    geojson_1966 = {
        "type": "FeatureCollection",
        "features": parent_1966_features
    }
    path_1966 = "data/processed/vidarbha_boundaries.geojson"
    public_path = "frontend/public/vidarbha_boundaries.geojson"
    
    with open(path_1966, "w", encoding="utf-8") as f:
        json.dump(geojson_1966, f)
    with open(public_path, "w", encoding="utf-8") as f:
        json.dump(geojson_1966, f)
        
    size_kb = os.path.getsize(path_1966) / 1024.0
    print(f"Saved 1966 boundaries to {path_1966} and {public_path} (Size: {size_kb:.1f} KB - target < 300 KB)")
    assert size_kb < 300.0, f"Boundary file size {size_kb} KB exceeds 300 KB limit"
    
    update_provenance("vidarbha_boundaries", {
        "source_name": "Census of India District Boundaries via DataMeet / GADM",
        "url": INDIA_GEOJSON_URL,
        "license": "Creative Commons Attribution-ShareAlike 2.0 (CC BY-SA 2.0) / ODbL",
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256,
        "features_count_modern": len(vidarbha_modern_features),
        "features_count_1966": len(parent_1966_features),
        "file_size_kb": round(size_kb, 1),
        "output_files": [modern_path, path_1966, public_path]
    })
    print("Boundaries provenance logged successfully.")

if __name__ == "__main__":
    prepare_boundaries()

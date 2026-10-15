import os
import json
import urllib.request
import urllib.error

# Ensure directories exist
os.makedirs('docs/samples', exist_ok=True)

print("Starting Phase 0 Data Audits...", flush=True)

# 1. NASA POWER API
def fetch_nasa_power():
    print("Fetching NASA POWER sample...", flush=True)
    url = "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR&community=AG&longitude=79.0&latitude=21.0&start=20200101&end=20200131&format=JSON"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            with open('docs/samples/nasa_power_sample.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("NASA POWER: Success", flush=True)
            return data
    except Exception as e:
        print(f"NASA POWER: Failed - {e}", flush=True)
        return None

# 2. World Bank Climate Knowledge Portal API
def fetch_world_bank():
    print("Fetching World Bank Climate sample...", flush=True)
    url = "https://climateknowledgeportal.worldbank.org/api/v1/cru-x0.5_climatology_tas_annual_climatology_mean_1991-2020/IND?_format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            with open('docs/samples/world_bank_sample.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("World Bank: Success", flush=True)
            return data
    except Exception as e:
        print(f"World Bank: Failed - {e}", flush=True)
        return None

# 3. FAOSTAT API (Using standard bulk or sample endpoint)
def fetch_faostat():
    print("Fetching FAOSTAT sample...", flush=True)
    url = "https://fenixservices.fao.org/faostat/api/v1/en/data/QC?area=100&element=5419&item=15&year=2020"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            with open('docs/samples/faostat_sample.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("FAOSTAT: Success", flush=True)
            return data
    except Exception as e:
        print(f"FAOSTAT: Failed - {e}", flush=True)
        return None

# 4. ICRISAT (Check access to DLD site)
def fetch_icrisat():
    print("Fetching ICRISAT DLD sample...", flush=True)
    url = "https://data.icrisat.org/dld/src/DLD_master_page.php"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode()
            with open('docs/samples/icrisat_dld_page.html', 'w', encoding='utf-8') as f:
                f.write(content[:5000]) # save snippet
            print("ICRISAT DLD: Success (Page reachable)", flush=True)
            return True
    except Exception as e:
        print(f"ICRISAT DLD: Failed - {e}", flush=True)
        return None

if __name__ == "__main__":
    nasa = fetch_nasa_power()
    wb = fetch_world_bank()
    fao = fetch_faostat()
    icr = fetch_icrisat()

    print("\nNetwork Access Summary:")
    print(f"NASA POWER: {'OK' if nasa else 'BLOCKED'}")
    print(f"World Bank: {'OK' if wb else 'BLOCKED'}")
    print(f"FAOSTAT: {'OK' if fao else 'BLOCKED'}")
    print(f"ICRISAT: {'OK' if icr else 'BLOCKED'}", flush=True)

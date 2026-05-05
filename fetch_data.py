"""
One-time data fetch script. Run this before starting the app:
    python fetch_data.py

Creates:
    data/cables.json        — full detail for every cable
    data/landing_points.json — every landing point with lat/lon (geocoded via Nominatim)

Re-running is safe: skips already-geocoded points and resumes from where it left off.
"""
import json, time, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; submarine-cables-app/1.0)"}
NOM_UA   = {"User-Agent": "submarine-cables-portfolio/1.0 contact:credechrome@gmail.com"}
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CABLES_PATH = os.path.join(DATA_DIR, "cables.json")
LP_PATH     = os.path.join(DATA_DIR, "landing_points.json")


# ── Step 1 : fetch individual cable detail ─────────────────────────────────────
def _fetch_cable(cable_id):
    try:
        r = requests.get(
            f"https://www.submarinecablemap.com/api/v3/cable/{cable_id}.json",
            timeout=15, headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [warn] {cable_id}: {e}")
        return None


def fetch_all_cables():
    if os.path.exists(CABLES_PATH):
        print(f"OK cables.json already exists, skipping fetch.")
        with open(CABLES_PATH, encoding="utf-8") as f:
            return json.load(f)

    print("Fetching cable list…")
    r = requests.get(
        "https://www.submarinecablemap.com/api/v3/cable/all.json",
        timeout=15, headers=HEADERS,
    )
    r.raise_for_status()
    cable_list = r.json()
    print(f"  {len(cable_list)} cables found. Fetching details (20 workers)…")

    results = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(_fetch_cable, c["id"]): c["id"] for c in cable_list}
        done = 0
        for future in as_completed(futures):
            cable_id = futures[future]
            data = future.result()
            if data:
                results[cable_id] = data
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(cable_list)}…")

    cables = []
    for c in results.values():
        def _split(v):
            if isinstance(v, list): return v
            if isinstance(v, str) and v: return [o.strip() for o in v.split(",") if o.strip()]
            return []

        cables.append({
            "id":          c.get("id", ""),
            "name":        c.get("name", ""),
            "rfs":         c.get("rfs", ""),
            "rfs_year":    c.get("rfs_year"),
            "length":      c.get("length", ""),
            "owners":      _split(c.get("owners", [])),
            "suppliers":   _split(c.get("suppliers", [])),
            "is_planned":  c.get("is_planned", False),
            "n_lp":        len(c.get("landing_points", [])),
            "landing_points": [
                {"id": lp["id"], "name": lp["name"], "country": lp.get("country", "")}
                for lp in c.get("landing_points", [])
            ],
        })

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CABLES_PATH, "w", encoding="utf-8") as f:
        json.dump(cables, f, ensure_ascii=False)
    print(f"  OK Saved {len(cables)} cables → {CABLES_PATH}")
    return cables


# ── Step 2 : extract unique landing points ──────────────────────────────────────
def extract_landing_points(cables):
    lp_map = {}  # id -> {id, name, country, cables: [cable_id, ...]}
    for c in cables:
        for lp in c.get("landing_points", []):
            lid = lp["id"]
            if lid not in lp_map:
                lp_map[lid] = {
                    "id":      lid,
                    "name":    lp["name"],
                    "country": lp.get("country", ""),
                    "cables":  [],
                }
            lp_map[lid]["cables"].append(c["id"])
    return lp_map


# ── Step 3 : geocode via Nominatim ─────────────────────────────────────────────
def geocode(name, country):
    for query in [f"{name}, {country}", country]:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                headers=NOM_UA,
                timeout=10,
            )
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
        time.sleep(1.1)
    return None, None


def geocode_landing_points(lp_map):
    # Load existing results to allow resuming
    existing = {}
    if os.path.exists(LP_PATH):
        with open(LP_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                existing[item["id"]] = item

    to_geocode = [lp for lid, lp in lp_map.items() if lid not in existing]
    total = len(lp_map)
    already = len(existing)
    print(f"  {already}/{total} already geocoded. Geocoding {len(to_geocode)} new points…")
    print(f"  (Nominatim rate limit: 1 req/s — estimated {len(to_geocode)} seconds)")

    for i, lp in enumerate(to_geocode):
        lat, lon = geocode(lp["name"], lp["country"])
        existing[lp["id"]] = {
            **lp,
            "lat": lat,
            "lon": lon,
            "n_cables": len(lp["cables"]),
        }
        time.sleep(1.1)
        if (i + 1) % 50 == 0 or (i + 1) == len(to_geocode):
            # Save progress after every 50 points
            with open(LP_PATH, "w", encoding="utf-8") as f:
                json.dump(list(existing.values()), f, ensure_ascii=False)
            print(f"  {already + i + 1}/{total} — saved progress")

    # Final save
    with open(LP_PATH, "w", encoding="utf-8") as f:
        json.dump(list(existing.values()), f, ensure_ascii=False)
    print(f"  OK Saved {len(existing)} landing points → {LP_PATH}")
    return list(existing.values())


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=== Step 1: Cables ===")
    cables = fetch_all_cables()
    print(f"  {len(cables)} cables loaded.")

    print("\n=== Step 2: Landing points ===")
    lp_map = extract_landing_points(cables)
    print(f"  {len(lp_map)} unique landing points found.")

    print("\n=== Step 3: Geocoding ===")
    geocode_landing_points(lp_map)

    print("\nDONE Done! You can now run: streamlit run app.py")

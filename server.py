import os, json
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rag_chain  import rag_generate_sql, rag_summarise
from vector_store import retrieve_context
from routing    import geocode_location, get_route
from intent     import detect_intent

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur  = conn.cursor()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

class QueryRequest(BaseModel):
    query: str

def is_safe(sql: str) -> bool:
    blocked = ["DROP","DELETE","INSERT","UPDATE","TRUNCATE"]
    return sql.upper().strip().startswith("SELECT") and not any(b in sql.upper() for b in blocked)

def find_nearest_hospitals(lat: float, lon: float, limit: int = 3) -> list:
    """Find nearest hospitals using PostGIS ST_Distance ordered query."""
    cur.execute("""
        SELECT id, name, type, beds, district,
               ST_AsGeoJSON(geom) AS geojson,
               ROUND(ST_Distance(geom::geography,
                   ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography)::numeric / 1000, 2
               ) AS distance_km
        FROM   hospitals
        ORDER  BY geom::geography <-> ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography
        LIMIT  %s
    """, (lon, lat, lon, lat, limit))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

@app.post("/api/geo-query")
async def geo_query(req: QueryRequest):

    # ── Step 1: Detect intent ──
    intent_data = detect_intent(req.query)
    intent      = intent_data.get("intent", "FILTER_HOSPITALS")
    location    = intent_data.get("location")

    # ── NEAREST HOSPITAL flow ──
    if intent in ("NEAREST_HOSPITAL", "ROUTE_TO_HOSPITAL") and location:

        # Geocode the user's location
        coords = geocode_location(location)
        if not coords:
            return {
                "sql": "",
                "summary": f"I couldn't find the location '{location}' on the map. Try being more specific, e.g. 'Hamidia Hospital Bhopal' or 'Indore Railway Station'.",
                "geojson": {"type":"FeatureCollection","features":[]},
                "route": None,
                "origin": None
            }

        origin_lat, origin_lon = coords

        # Find nearest hospitals from DB
        nearest = find_nearest_hospitals(origin_lat, origin_lon, limit=3)
        if not nearest:
            return {
                "sql": "",
                "summary": "No hospitals found near that location.",
                "geojson": {"type":"FeatureCollection","features":[]},
                "route": None,
                "origin": {"lat": origin_lat, "lon": origin_lon, "name": location}
            }

        # Get route to the nearest hospital
        nearest_hospital = nearest[0]
        hospital_geojson = json.loads(nearest_hospital["geojson"])
        dest_lon = hospital_geojson["coordinates"][0]
        dest_lat = hospital_geojson["coordinates"][1]

        route = get_route(origin_lon, origin_lat, dest_lon, dest_lat)

        # Build features for all 3 nearest hospitals
        features = []
        for i, h in enumerate(nearest):
            hgj = json.loads(h["geojson"])
            features.append({
                "type": "Feature",
                "geometry": hgj,
                "properties": {
                    k: v for k, v in h.items()
                    if k not in ("geojson","geom")
                } | {"nearest_rank": i + 1}
            })

        # Build summary
        h = nearest[0]
        summary = f"Nearest hospital to {location}:\n"
        summary += f"1. {h['name']} — {h['distance_km']} km away ({h['type']}, {h['beds']} beds)"
        if route:
            summary += f"\nRoute: {route['distance_km']} km · {int(route['duration_min'])} min drive"
        if len(nearest) > 1:
            summary += f"\n\nOther nearby hospitals:"
            for h2 in nearest[1:]:
                summary += f"\n• {h2['name']} — {h2['distance_km']} km ({h2['type']})"

        sql = f"-- Nearest hospitals to {location} ({origin_lat:.4f}, {origin_lon:.4f})\n"
        sql += f"SELECT name, type, beds, ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint({origin_lon},{origin_lat}),4326)::geography)/1000 AS km FROM hospitals ORDER BY geom::geography <-> ST_SetSRID(ST_MakePoint({origin_lon},{origin_lat}),4326)::geography LIMIT 3;"

        return {
            "sql":     sql,
            "summary": summary,
            "geojson": {"type": "FeatureCollection", "features": features},
            "route":   route,
            "origin":  {"lat": origin_lat, "lon": origin_lon, "name": location}
        }

    # ── FILTER / GENERAL flow (RAG) ──
    context   = retrieve_context(req.query, k=4)
    knowledge = context["knowledge"]

    sql, schemas_used = rag_generate_sql(req.query)

    if not sql:
        return {
            "sql": "",
            "summary": "I couldn't find a relevant data layer for your query.",
            "geojson": {"type":"FeatureCollection","features":[]},
            "route": None, "origin": None
        }

    if not is_safe(sql):
        return {
            "sql": sql, "summary": "Query blocked for safety.",
            "geojson": {"type":"FeatureCollection","features":[]},
            "route": None, "origin": None
        }

    try:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        summary  = rag_summarise(req.query, rows, knowledge)
        features = []
        for row in rows:
            gj = row.get("geojson")
            if gj:
                features.append({
                    "type": "Feature",
                    "geometry": json.loads(gj),
                    "properties": {k:v for k,v in row.items() if k not in ("geojson","geom")}
                })
        return {
            "sql": sql, "summary": summary,
            "geojson": {"type":"FeatureCollection","features":features},
            "route": None, "origin": None,
            "layers_used": [s["layer"] for s in schemas_used]
        }

    except Exception as e:
        conn.rollback()
        return {
            "sql": sql,
            "summary": f"Query error: {str(e)}",
            "geojson": {"type":"FeatureCollection","features":[]},
            "route": None, "origin": None
        }

@app.post("/api/rebuild-index")
def rebuild_index():
    from vector_store import build_vector_store
    build_vector_store()
    return {"status": "Vector store rebuilt"}

@app.get("/api/health")
def health():
    return {"status": "ok"}



@app.get("/")
def root():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "API root. Use /api/health or /api/geo-query."}


@app.get("/index.html")
def index_html():
    return RedirectResponse(url="/static/index.html")

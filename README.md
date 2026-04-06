# 🏥 MP Geo-Portal — Hospital Intelligence System

> An AI-powered geospatial chatbot for the **Madhya Pradesh Government GIS Portal** that translates natural language queries into PostGIS spatial SQL, renders results on an interactive map, and provides driving routes to the nearest hospitals.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL+PostGIS-4169E1?style=flat&logo=postgresql&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green?style=flat)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat&logo=openai&logoColor=white)

---

## 📌 Overview

This system bridges the gap between natural language and structured GIS queries. Instead of requiring users to know SQL or GIS tools, decision-makers and field officers can simply type or speak a question — the AI handles everything else.

**Example queries the system understands:**
- `"Show all government hospitals in Bhopal"`
- `"Which hospitals have more than 500 beds?"`
- `"Find the nearest hospital from Collectorate Bhopal"`
- `"List all PHC and CHC hospitals in Narmadapuram"`
- `"What is the total bed capacity in Jabalpur?"`

---

## 🏗️ Architecture

```
User Query (NLP)
      │
      ▼
Intent Detection (LangChain + GPT-4o-mini)
      │
      ├─── FILTER query ──► RAG Engine
      │                        │
      │                   pgvector similarity search
      │                        │
      │                   Schema retrieval → GPT-4o → PostGIS SQL
      │                        │
      │                   PostgreSQL + PostGIS execution
      │
      └─── NEAREST query ──► Geocoding (Nominatim OSM)
                                │
                           PostGIS ST_Distance ordering
                                │
                           OpenRouteService → Driving route
                                │
                           Map render (Leaflet.js)
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Leaflet.js, JavaScript |
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **AI / NLP** | OpenAI GPT-4o, GPT-4o-mini |
| **RAG Framework** | LangChain, LangChain-OpenAI, LangChain-Community |
| **Vector Search** | pgvector (PostgreSQL extension) |
| **Spatial Database** | PostgreSQL 16 + PostGIS 3.4 |
| **Routing** | OpenRouteService Directions API v2 |
| **Geocoding** | OpenStreetMap Nominatim |
| **Hospital Data** | OpenStreetMap Overpass API |
| **Containerization** | Docker (postgis/postgis:16-3.4) |

---

## 📁 Project Structure

```
MPGEO/
├── static/
│   ├── index.html          # Frontend map + chat UI
│   ├── main.js             # JS utilities
│   └── backup.js           # JS backup
├── server.py               # FastAPI app — main entry point
├── rag_chain.py            # LangChain RAG pipeline (SQL generation + summarisation)
├── vector_store.py         # pgvector embedding store (layer metadata + knowledge docs)
├── intent.py               # Query intent classifier (NEAREST / FILTER / GENERAL)
├── routing.py              # Geocoding + OpenRouteService driving directions
├── fetch_osm_hospitals.py  # One-time script: pull real hospitals from OpenStreetMap
├── prototype.py            # CLI prototype (for testing without the web UI)
├── .env                    # Environment variables (not committed)
├── .gitignore
└── requirements.txt
```

---

## ⚙️ Prerequisites

- Python 3.10+
- Docker Desktop (running)
- Git

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/mp-geo-portal.git
cd mp-geo-portal/mpgeo
```

### 2. Start the PostgreSQL + PostGIS + pgvector Docker container

```bash
docker run -d \
  --name mp-geo \
  -e POSTGRES_PASSWORD=postgres \
  -p 5433:5432 \
  postgis/postgis:16-3.4
```

> **Windows CMD** (single line):
> ```cmd
> docker run -d --name mp-geo -e POSTGRES_PASSWORD=postgres -p 5433:5432 postgis/postgis:16-3.4
> ```

### 3. Enable PostGIS and pgvector extensions

Connect to the database in pgAdmin or psql and run:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
SELECT PostGIS_Version();
```

### 4. Create the hospitals table and seed mock data

Run this in pgAdmin Query Tool:

```sql
CREATE TABLE IF NOT EXISTS hospitals (
    id        SERIAL PRIMARY KEY,
    name      TEXT,
    type      TEXT,
    beds      INT,
    district  TEXT,
    geom      GEOMETRY(Point, 4326)
);

INSERT INTO hospitals (name, type, beds, district, geom) VALUES
('Hamidia Hospital',           'Government', 1500, 'Bhopal',       ST_SetSRID(ST_MakePoint(77.4126, 23.2599), 4326)),
('AIIMS Bhopal',               'Government',  960, 'Bhopal',       ST_SetSRID(ST_MakePoint(77.3823, 23.1993), 4326)),
('Bhopal Memorial Hospital',   'Government',  400, 'Bhopal',       ST_SetSRID(ST_MakePoint(77.4720, 23.2850), 4326)),
('MY Hospital Indore',         'Government', 1200, 'Indore',       ST_SetSRID(ST_MakePoint(75.8577, 22.7196), 4326)),
('CHL Hospital Indore',        'Private',     350, 'Indore',       ST_SetSRID(ST_MakePoint(75.8839, 22.7322), 4326)),
('Apollo Indore',              'Private',     300, 'Indore',       ST_SetSRID(ST_MakePoint(75.9100, 22.7500), 4326)),
('Gajra Raja Medical College', 'Government',  800, 'Gwalior',      ST_SetSRID(ST_MakePoint(78.1828, 26.2124), 4326)),
('Kamla Raja Hospital',        'Government',  600, 'Gwalior',      ST_SetSRID(ST_MakePoint(78.1750, 26.2200), 4326)),
('NSCB Medical College',       'Government',  900, 'Jabalpur',     ST_SetSRID(ST_MakePoint(79.9864, 23.1815), 4326)),
('Victoria Hospital Jabalpur', 'Government',  450, 'Jabalpur',     ST_SetSRID(ST_MakePoint(79.9420, 23.1650), 4326)),
('District Hospital Sagar',    'Government',  300, 'Sagar',        ST_SetSRID(ST_MakePoint(78.7378, 23.8388), 4326)),
('District Hospital Rewa',     'Government',  350, 'Rewa',         ST_SetSRID(ST_MakePoint(81.2966, 24.5362), 4326)),
('PHC Hoshangabad',            'PHC',          30, 'Narmadapuram', ST_SetSRID(ST_MakePoint(77.7172, 22.7539), 4326)),
('CHC Itarsi',                 'CHC',          50, 'Narmadapuram', ST_SetSRID(ST_MakePoint(77.7653, 22.6156), 4326)),
('District Hospital Ujjain',   'Government',  400, 'Ujjain',       ST_SetSRID(ST_MakePoint(75.7849, 23.1765), 4326));
```

### 5. Create a Python virtual environment

```cmd
python -m venv mpgeo
mpgeo\Scripts\activate
```

### 6. Install dependencies

```cmd
pip install fastapi uvicorn psycopg2-binary python-dotenv openai langchain langchain-openai langchain-community pgvector tiktoken requests sqlalchemy
```

Or using requirements.txt:

```cmd
pip install -r requirements.txt
```

### 7. Configure environment variables

Create a `.env` file in the `mpgeo` folder:

```env
OPENAI_API_KEY=sk-your-openai-key-here
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres
ORS_API_KEY=your-openrouteservice-key-here
```

> **Get your API keys:**
> - OpenAI: https://platform.openai.com/api-keys
> - OpenRouteService (free): https://openrouteservice.org/dev/#/login

### 8. Build the RAG vector store

```cmd
python vector_store.py
```

Expected output:
```
Vector store built — 5 documents embedded.
```

### 9. (Optional) Pull real hospital data from OpenStreetMap

```cmd
python fetch_osm_hospitals.py
```

Expected output:
```
Found 280 hospitals from OSM
Inserted 265 hospitals | Total in DB: 280
```

---

## ▶️ Running the Application

```cmd
cd C:\Users\YourName\Desktop\mp_geo\mpgeo
mpgeo\Scripts\activate
uvicorn server:app --reload
```

Open your browser at:

```
http://localhost:8000/static/index.html
```

---

## 💬 Example Queries

| Query | What happens |
|---|---|
| `Show all government hospitals in Bhopal` | Filters by district + type, plots markers |
| `Which hospitals have more than 500 beds?` | Filters by bed count, lists results |
| `Show all PHC and CHC in MP` | Multi-type filter across all districts |
| `Find nearest hospital from Collectorate Bhopal` | Geocodes location → PostGIS nearest → ORS route |
| `Total bed capacity in Jabalpur` | Aggregates beds, replies in text |
| `List private hospitals in Indore` | Type + district filter |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/geo-query` | Main NLP query endpoint |
| `POST` | `/api/rebuild-index` | Rebuild pgvector embeddings |
| `GET` | `/api/health` | Health check |
| `GET` | `/static/index.html` | Frontend UI |

### Example request

```bash
curl -X POST http://localhost:8000/api/geo-query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all government hospitals in Bhopal"}'
```

### Example response

```json
{
  "sql": "SELECT id, name, type, beds, district, ST_AsGeoJSON(geom) AS geojson FROM hospitals WHERE district ILIKE '%Bhopal%' AND type ILIKE '%Government%' LIMIT 100",
  "summary": "3 government hospitals found in Bhopal:\n1. Hamidia Hospital — 1500 beds (Government)\n2. AIIMS Bhopal — 960 beds (Government)\n3. Bhopal Memorial Hospital — 400 beds (Government)\nTotal beds: 2860",
  "geojson": { "type": "FeatureCollection", "features": [...] },
  "route": null,
  "origin": null
}
```

---

## 🗺️ Features

- **NLP to PostGIS SQL** — Natural language queries converted to spatial SQL via GPT-4o
- **RAG Pipeline** — pgvector semantic search auto-discovers relevant database layers
- **Intent Detection** — Automatically routes between filter queries and nearest-hospital routing
- **Nearest Hospital + Route** — Geocodes any location, finds nearest hospitals via PostGIS, draws driving route via OpenRouteService
- **Interactive Map** — Leaflet.js with colour-coded hospital markers, popups, zoom-to-extent
- **Results Panel** — Clickable hospital cards with zoom-to-location
- **Live Stats HUD** — Total hospitals, filtered count, total beds shown on map overlay
- **Hindi Header** — Designed for MP government context

---

## 🐛 Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'langchain_openai'` | Run `pip install langchain-openai` inside activated venv |
| `Cannot reach server` in browser | Make sure uvicorn is running: `uvicorn server:app --reload` |
| Map shows wrong location | Check `setView([23.5, 78.5], 7)` in `index.html` |
| `relation "hospitals" does not exist` | Run the SQL seed script in pgAdmin |
| `extension "vector" is not available` | Use `postgis/postgis:16-3.4` Docker image, not `ankane/pgvector` |
| ORS routing returns null | Check `ORS_API_KEY` in `.env` — must have `ORS_API_KEY=` prefix |
| `CardinalityViolation` error | Run `DELETE FROM water_bodies WHERE id NOT IN (SELECT MIN(id) FROM water_bodies GROUP BY name)` |

---

## 📄 License

This project was developed as a prototype for the **Madhya Pradesh State Geo-Portal** under the Department of Science and Technology, Government of Madhya Pradesh.

---

## 🙏 Acknowledgements

- [OpenStreetMap](https://www.openstreetmap.org/) — Hospital data via Overpass API
- [OpenRouteService](https://openrouteservice.org/) — Driving directions API
- [PostGIS](https://postgis.net/) — Spatial database extension
- [LangChain](https://langchain.com/) — RAG framework
- [Leaflet.js](https://leafletjs.com/) — Interactive maps

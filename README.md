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

---

## Setup & Installation

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

### 4. Create a Python virtual environment

```cmd
python -m venv mpgeo
mpgeo\Scripts\activate
```

### 5. Install dependencies

Use requirements.txt:

```cmd
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the `mpgeo` folder:

```env
OPENAI_API_KEY=sk-your-openai-key-here
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres
ORS_API_KEY=your-openrouteservice-key-here
```

> **Get your API keys:**
> - OpenAI: https://platform.openai.com/api-keys
> - OpenRouteService (free): https://openrouteservice.org/dev/#/login

### 7. Build the RAG vector store

```cmd
python vector_store.py
```

Expected output:
```
Vector store built — 5 documents embedded.
```

### 8. (Optional) Pull real hospital data from OpenStreetMap

```cmd
python fetch_osm_hospitals.py
```

Expected output:
```
Found 280 hospitals from OSM
Inserted 265 hospitals | Total in DB: 280
```

---

## Running the Application

```cmd
cd C:\Users\YourName\Desktop\mp_geo\mpgeo
mpgeo\Scripts\activate
uvicorn server:app --reload
```

Open your browser at:

```
http://localhost:8000/static/index.html
```


## License

This project was developed as a prototype for the **Madhya Pradesh State Geo-Portal** under the Department of Science and Technology, Government of Madhya Pradesh.

---

## Acknowledgements

- [OpenStreetMap](https://www.openstreetmap.org/) — Hospital data via Overpass API
- [OpenRouteService](https://openrouteservice.org/) — Driving directions API
- [PostGIS](https://postgis.net/) — Spatial database extension
- [LangChain](https://langchain.com/) — RAG framework
- [Leaflet.js](https://leafletjs.com/) — Interactive maps

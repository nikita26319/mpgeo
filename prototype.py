import os, json
import openai
import psycopg2
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
conn   = psycopg2.connect(os.getenv("DATABASE_URL"))
cur    = conn.cursor()

SCHEMA = """
Table: land_use
Columns: id (int), name (text), land_type (text), area_sqm (float), geom (geometry point, SRID 4326)
Values for land_type: 'Encroached', 'Forest', 'Agricultural', 'Urban'

Table: water_bodies
Columns: id (int), name (text), geom (geometry linestring, SRID 4326)
Example river name: 'Narmada'
"""

SYSTEM_PROMPT = f"""
You are a PostGIS SQL expert for the Madhya Pradesh Geo-Portal.
Given a natural language query, generate a valid PostGIS SQL SELECT query.

RULES:
- Use ST_DWithin with geography cast for distance queries (distances in metres)
- For named places use: (SELECT ST_Union(geom) FROM water_bodies WHERE name ILIKE '%name%')
- Default buffer distance is 5000 metres unless user specifies
- Add LIMIT 100
- Return ONLY the raw SQL — no markdown, no explanation, no code fences

SCHEMA:
{SCHEMA}
"""

def is_safe(sql: str) -> bool:
    blocked = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE"]
    sql_up  = sql.upper()
    return sql_up.strip().startswith("SELECT") and not any(b in sql_up for b in blocked)

def generate_sql(user_query: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_query}
        ]
    )
    return resp.choices[0].message.content.strip()

def ST_Union(sql: str) -> list:
    if not is_safe(sql):
        raise ValueError("Query failed safety check.")
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def summarise(user_query: str, results: list) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""
User asked: "{user_query}"
Query returned {len(results)} results: {json.dumps(results, default=str)[:1000]}
Write a 2-sentence plain-English summary for a government official.
"""}]
    )
    return resp.choices[0].message.content

# ── Interactive mode ──
print("\n MP Geo-Portal NLP Prototype")
print("=" * 40)
print("Type a query in plain English. Type 'exit' to quit.\n")

while True:
    query = input("You: ").strip()
    if query.lower() == "exit":
        break
    if not query:
        continue

    print("\nGenerating SQL...")
    sql = generate_sql(query)
    print(f"SQL: {sql}\n")

    results = ST_Union(sql)
    print(f"Found {len(results)} result(s):")
    for r in results:
        print(f"  {r}")

    summary = summarise(query, results)
    print(f"\nSummary: {summary}")
    print("-" * 40 + "\n")
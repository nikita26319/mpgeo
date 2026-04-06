import os, json
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.pgvector import PGVector
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME   = "mp_geoportal_layers"
CONNECTION_STRING = os.getenv("DATABASE_URL")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

LAYER_METADATA = [
    {
        "layer": "hospitals",
        "description": "Government, private, PHC and CHC hospitals across Madhya Pradesh with bed capacity",
        "keywords": "hospital health clinic medical PHC CHC beds district healthcare facility",
        "attributes": {
            "id": "int", "name": "text", "type": "text",
            "beds": "int", "district": "text", "geom": "geometry point SRID 4326"
        },
        "type_values":     ["Government", "Private", "PHC", "CHC", "District"],
        "district_values": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Sagar", "Rewa", "Ujjain", "Narmadapuram"],
        "notes": "Hoshangabad was renamed to Narmadapuram in 2022"
    },
]

KNOWLEDGE_DOCS = [
    {
        "title": "MP Hospital Network Overview",
        "content": """Madhya Pradesh has a three-tier hospital network.
Primary Health Centres (PHC) serve rural populations under 30,000.
Community Health Centres (CHC) serve populations of 80,000-120,000.
District Hospitals serve entire districts.
Government hospitals are free for all citizens.
AIIMS Bhopal is a premier central government institute.
Hamidia Hospital in Bhopal is the largest government hospital with 1500 beds.
MY Hospital in Indore is the largest government hospital in Indore with 1200 beds."""
    },
    {
        "title": "MP District Health Statistics",
        "content": """Bhopal district has the highest concentration of hospitals in MP.
Indore district has the most private hospitals.
Narmadapuram (formerly Hoshangabad) district has PHC and CHC facilities.
Gwalior has Gajra Raja Medical College, a major teaching hospital.
Jabalpur has NSCB Medical College as its premier institution.
Rural districts like Sagar and Rewa rely primarily on government hospitals."""
    },
    {
        "title": "Hospital Naming and Administrative Notes",
        "content": """Hoshangabad district was officially renamed to Narmadapuram in 2022.
All queries about Hoshangabad should be resolved to Narmadapuram.
MP Geo-Portal uses the official 2022 district names.
District Hospital refers to the main government hospital serving an entire district."""
    }
]


def build_vector_store():
    docs = []

    for layer in LAYER_METADATA:
        text = f"""
Layer: {layer['layer']}
Description: {layer['description']}
Keywords: {layer['keywords']}
Attributes: {json.dumps(layer['attributes'])}
Type values: {layer.get('type_values', [])}
District values: {layer.get('district_values', [])}
Notes: {layer.get('notes', '')}
        """.strip()

        docs.append(Document(
            page_content=text,
            metadata={
                "type":        "layer_schema",
                "layer":       layer["layer"],
                "description": layer["description"]
            }
        ))

    for doc in KNOWLEDGE_DOCS:
        docs.append(Document(
            page_content=doc["content"],
            metadata={
                "type":  "knowledge",
                "title": doc["title"]
            }
        ))

    store = PGVector.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        pre_delete_collection=True
    )
    print(f"Vector store built — {len(docs)} documents embedded.")
    return store


def get_vector_store():
    return PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings
    )


def retrieve_context(query: str, k: int = 4) -> dict:
    store   = get_vector_store()
    results = store.similarity_search_with_score(query, k=k)

    schemas   = []
    knowledge = []

    for doc, score in results:
        if doc.metadata.get("type") == "layer_schema":
            schemas.append({
                "layer":   doc.metadata["layer"],
                "content": doc.page_content,
                "score":   round(score, 3)
            })
        elif doc.metadata.get("type") == "knowledge":
            knowledge.append({
                "title":   doc.metadata["title"],
                "content": doc.page_content,
                "score":   round(score, 3)
            })

    return {"schemas": schemas, "knowledge": knowledge}


if __name__ == "__main__":
    build_vector_store()
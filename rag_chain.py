import os, json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from vector_store import retrieve_context
from dotenv import load_dotenv

load_dotenv()

llm_sql = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

llm_answer = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a PostGIS SQL expert for the Madhya Pradesh Geo-Portal.
Generate a valid PostGIS SQL SELECT query based on the retrieved schema below.

RETRIEVED SCHEMA:
{schema}

RULES:
- Use ONLY the table names listed in the schema — never invent table names
- Use ST_DWithin with geography cast for distance queries (metres)
- Default search radius 10000 metres unless specified
- Always include ST_AsGeoJSON(geom) AS geojson in SELECT
- Always include name, type, beds, district in SELECT where those columns exist
- NEVER use SUM(), COUNT(), GROUP BY — always return individual rows
- For district filters: WHERE district ILIKE '%value%'
- For type filters:     WHERE type ILIKE '%value%'
- Add LIMIT 100
- Return ONLY raw SQL — no markdown, no explanation, no code fences"""),
    ("human", "{query}")
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a concise GIS assistant for the MP Hospital Portal.
Use the knowledge context and query results below to answer the user.

KNOWLEDGE CONTEXT:
{knowledge}

QUERY RESULTS:
{results}

RULES:
- NO greetings, NO sign-offs, NO Dear, NO Best regards
- NO markdown bold, NO asterisks
- Start directly with the answer
- List items as: 1. Name — X beds (Type)
- Include total beds if relevant
- If results are empty, use knowledge context to answer conversationally
- Keep it under 8 lines"""),
    ("human", "{query}")
])

sql_chain    = SQL_PROMPT    | llm_sql    | StrOutputParser()
answer_chain = ANSWER_PROMPT | llm_answer | StrOutputParser()


def rag_generate_sql(user_query: str) -> tuple:
    context = retrieve_context(user_query, k=3)
    schemas = context["schemas"]

    if not schemas:
        return "", []

    schema_text = "\n\n---\n\n".join(s["content"] for s in schemas)
    sql = sql_chain.invoke({"schema": schema_text, "query": user_query})
    return sql.strip(), schemas


def rag_summarise(user_query: str, results: list, knowledge: list) -> str:
    clean   = [{k: v for k, v in r.items() if k not in ('geom', 'geojson')} for r in results]
    total_b = sum(r.get('beds') or 0 for r in clean)

    knowledge_text = "\n\n".join(
        f"{k['title']}:\n{k['content']}" for k in knowledge
    ) if knowledge else "No additional context available."

    results_text = f"{len(clean)} results. Total beds: {total_b}.\n{json.dumps(clean, default=str)[:1500]}"

    return answer_chain.invoke({
        "knowledge": knowledge_text,
        "results":   results_text,
        "query":     user_query
    })
import os, json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from vector_store import retrieve_context
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an intent classifier for a hospital GIS portal.
Classify the user query into one of these intents:

- NEAREST_HOSPITAL: user wants the nearest hospital FROM a specific location
- ROUTE_TO_HOSPITAL: user wants directions/route to a specific hospital
- FILTER_HOSPITALS: user wants to filter/list hospitals by type, district, beds
- GENERAL_QUESTION: general question about hospitals, no spatial query needed

Also extract:
- location: the origin location mentioned (or null)
- hospital_name: specific hospital name mentioned (or null)
- filters: any filters like type, district, beds (or null)

Respond ONLY as valid JSON like:
{
  "intent": "NEAREST_HOSPITAL",
  "location": "Collectorate Bhopal",
  "hospital_name": null,
  "filters": null
}"""),
    ("human", "{query}")
])

intent_chain = INTENT_PROMPT | llm | StrOutputParser()

def detect_intent(query: str) -> dict:
    import json
    try:
        raw = intent_chain.invoke({"query": query})
        # Strip markdown fences if present
        raw = raw.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"Intent detection error: {e}")
        return {"intent": "FILTER_HOSPITALS", "location": None, "hospital_name": None, "filters": None}
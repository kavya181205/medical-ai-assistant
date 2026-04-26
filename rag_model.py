import re
from typing import TypedDict, List

from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from langchain_huggingface import (
    HuggingFaceEndpoint,
    ChatHuggingFace,
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import FAISS
from langchain_tavily import TavilySearch

load_dotenv()

# --------------------------------------------------
# LLM
# --------------------------------------------------

model = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0,
    max_new_tokens=512
)

llm = ChatHuggingFace(llm=model)

# --------------------------------------------------
# EMBEDDINGS + VECTOR DATABASE
# --------------------------------------------------

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = FAISS.load_local(
    "data/faiss_index",
    embedding,
    allow_dangerous_deserialization=True
)

retriever = db.as_retriever(search_kwargs={"k": 4})

print("Vector database ready")

# --------------------------------------------------
# TAVILY SEARCH
# --------------------------------------------------

tavily = TavilySearch(max_results=5)

# --------------------------------------------------
# STATE
# --------------------------------------------------

class State(TypedDict):

    question: str
    predicted_disease: str | None

    docs: List[Document]
    good_docs: List[Document]

    verdict: str

    web_query: str
    web_docs: List[Document]

    refined_context: str

    answer: str


# --------------------------------------------------
# REMOVE REPETITION FUNCTION
# --------------------------------------------------

def remove_repetition(text):

    sentences = text.split(".")
    seen = set()
    result = []

    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            result.append(s)

    return ". ".join(result)




def retrieve_node(state: State):

    query = state["question"]

    if state.get("predicted_disease"):
        query += f" disease {state['predicted_disease']} symptoms treatment"

    docs = retriever.invoke(query)

    return {"docs": docs}


eval_prompt = ChatPromptTemplate.from_messages([
(
    "system",
    "You are a document relevance grader. Respond only YES or NO."
),
(
        "human",
        """
        Question: {question}

        Document:
        {doc}
        """
)
])


def eval_docs_node(state: State):

    good_docs = []

    for d in state["docs"]:

        result = (eval_prompt | llm).invoke({
            "question": state["question"],
            "doc": d.page_content
        })

        if "yes" in result.content.lower():
            good_docs.append(d)

    verdict = "CORRECT" if good_docs else "INCORRECT"

    return {
        "good_docs": good_docs,
        "verdict": verdict
    }


rewrite_prompt = ChatPromptTemplate.from_messages([
(
    "system",
    "Rewrite the medical question as a detailed web search query including symptoms and diseases."
),
(
    "human",
    "{question}"
)
])


def rewrite_query_node(state: State):

    result = (rewrite_prompt | llm).invoke({
        "question": state["question"]
    })

    return {"web_query": result.content}


# --------------------------------------------------
# WEB SEARCH NODE
# --------------------------------------------------

def web_search_node(state: State):

    response = tavily.invoke({
        "query": state["web_query"]
    })

    web_docs = []

    # Handle both Tavily response formats
    if isinstance(response, list):
        results = response
    elif isinstance(response, dict) and "results" in response:
        results = response["results"]
    else:
        results = []

    for r in results:

        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "")

        text = f"""
TITLE: {title}
URL: {url}

CONTENT:
{content}
"""

        web_docs.append(Document(page_content=text))

    return {"web_docs": web_docs}


def refine_node(state: State):

    if state["verdict"] == "CORRECT":
        docs = state["good_docs"]
    else:
        docs = state["web_docs"]

    # remove duplicate documents
    unique = set()
    filtered_docs = []

    for d in docs:
        if d.page_content not in unique:
            unique.add(d.page_content)
            filtered_docs.append(d)

    context = "\n\n".join(d.page_content for d in filtered_docs)

    # limit context size
    context = context[:4000]

    return {"refined_context": context}


# --------------------------------------------------
# FINAL ANSWER GENERATION
# --------------------------------------------------

answer_prompt = ChatPromptTemplate.from_messages([
(
"system",
"""
You are a medical AI assistant.

Answer using the provided context.

Rules:
- Give a clear medical explanation
- Do NOT repeat sentences
- Summarize the information
- If information is missing say "I don't know"

This system provides educational information only and
is not a substitute for professional medical advice.
"""
),
(
"human",
"""
Question:
{question}

Context:
{context}
"""
)
])


def generate_node(state: State):

    result = (answer_prompt | llm).invoke({
        "question": state["question"],
        "context": state["refined_context"]
    })

    answer = remove_repetition(result.content)

    return {"answer": answer}


# --------------------------------------------------
# ROUTING FUNCTION
# --------------------------------------------------

def route_after_eval(state: State):

    if state["verdict"] == "CORRECT" and len(state["good_docs"]) >= 2:
        return "refine"

    return "rewrite_query"


# --------------------------------------------------
# BUILD GRAPH
# --------------------------------------------------

graph = StateGraph(State)

graph.add_node("retrieve", retrieve_node)
graph.add_node("eval_docs", eval_docs_node)
graph.add_node("rewrite_query", rewrite_query_node)
graph.add_node("web_search", web_search_node)
graph.add_node("refine", refine_node)
graph.add_node("generate", generate_node)

graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "eval_docs")

graph.add_conditional_edges(
    "eval_docs",
    route_after_eval,
    {
        "refine": "refine",
        "rewrite_query": "rewrite_query"
    }
)

graph.add_edge("rewrite_query", "web_search")
graph.add_edge("web_search", "refine")

graph.add_edge("refine", "generate")
graph.add_edge("generate", END)

# --------------------------------------------------
# DATABASE CHECKPOINTER
# --------------------------------------------------

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres"


def knowledge_agent(state):

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:

        checkpointer.setup()

        graph_builder = graph.compile(checkpointer=checkpointer)

        config = {
            "configurable": {
                "thread_id": "medical_thread"
            }
        }

        result = graph_builder.invoke(state, config=config)

    return result["answer"]
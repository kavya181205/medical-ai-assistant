import asyncio
import uuid

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import conn, cursor
from symptom_agent import symptom_agent_detect, predict_disease_api
from rag_model import knowledge_agent

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# -----------------------------
# Session memory
# -----------------------------
sessions = {}


# -----------------------------
# Enable CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/health")
def health():
    return {"status": "running"}


# -----------------------------
# CHAT ENDPOINT
# -----------------------------
@app.post("/chat")
async def chat(req: ChatRequest):

    # protect against very long messages
    if len(req.message) > 500:
        return {"response": "Message too long."}

    # create thread if missing
    if not req.thread_id:
        req.thread_id = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO conversations(thread_id) VALUES (?)",
            (req.thread_id,)
        )
        conn.commit()

    # initialize session safely
    session = sessions.setdefault(req.thread_id, {
        "symptoms": [],
        "edit_mode": False
    })

    message = req.message.lower()

    print("User:", req.message)
    print("Thread:", req.thread_id)


    async def generate():

        # -----------------------------
        # EDIT MODE
        # -----------------------------
        if session["edit_mode"]:

            if message == "add":

                response = "Please type the symptoms you want to add."

            elif message == "remove":

                symptoms = session["symptoms"]

                symptom_list = "\n".join(
                    [f"- {s.replace('_',' ')}" for s in symptoms]
                )

                response = f"""
Current detected symptoms:

{symptom_list}

Type the symptom you want to remove.
"""

            else:

                sym = message.replace(" ", "_")

                symptoms = session["symptoms"]

                if sym in symptoms:

                    symptoms.remove(sym)

                    symptom_text = "\n".join(
                        [f"- {s.replace('_',' ')}" for s in symptoms]
                    )

                    response = f"""
Updated Symptoms:

{symptom_text}

Are these correct now? (yes/no)
"""

                    session["edit_mode"] = False

                else:

                    # prevent duplicates
                    if sym not in symptoms:
                        symptoms.append(sym)

                    response = f"Added symptom: {message}"


        # -----------------------------
        # CONFIRM SYMPTOMS
        # -----------------------------
        elif session["symptoms"]:

            if message in ["yes", "y"]:

                symptoms = session["symptoms"]

                result = predict_disease_api(symptoms)

                predicted = result["predicted_disease"]

                pred_list = "\n".join(
                    [f"{d} ({round(s*100,2)}%)"
                     for d, s in result["top_predictions"]]
                )

                # emergency detection
                emergency_note = ""

                if result.get("emergency"):
                    emergency_note = "\n⚠️ This may require urgent medical attention.\n"

                rag_answer = knowledge_agent({
                    "question": predicted,
                    "predicted_disease": predicted
                })

                response = f"""
Predicted Disease: {predicted}

Top Predictions:
{pred_list}
{emergency_note}

Medical Information:
{rag_answer}
"""

                # clear session after diagnosis
                sessions.pop(req.thread_id, None)

            elif message in ["no", "n"]:

                session["edit_mode"] = True

                response = """
Detected symptoms may be incorrect.

Type:
add → to add more symptoms
remove → to remove detected symptoms
"""

            else:

                response = "Please reply with yes or no."


        # -----------------------------
        # DETECT SYMPTOMS
        # -----------------------------
        else:

            detect = symptom_agent_detect(req.message)

            symptoms = detect["symptoms"]

            if symptoms:

                session["symptoms"] = symptoms

                symptom_text = "\n".join(
                    [f"- {s.replace('_',' ')}" for s in symptoms]
                )

                response = f"""
Detected Symptoms:
{symptom_text}

Are these correct? (yes/no)
"""

            else:

                response = knowledge_agent({
                    "question": req.message,
                    "predicted_disease": None
                })


        # -----------------------------
        # SAVE CHAT
        # -----------------------------
        cursor.execute(
            "INSERT INTO messages(thread_id,role,content) VALUES (?,?,?)",
            (req.thread_id, "user", req.message)
        )

        cursor.execute(
            "INSERT INTO messages(thread_id,role,content) VALUES (?,?,?)",
            (req.thread_id, "assistant", response)
        )

        conn.commit()


        # -----------------------------
        # STREAM RESPONSE
        # -----------------------------
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.01)


    return StreamingResponse(generate(), media_type="text/plain")


# -----------------------------
# NEW CHAT
# -----------------------------
@app.post("/new_chat")
def new_chat():

    thread_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO conversations(thread_id) VALUES (?)",
        (thread_id,)
    )

    conn.commit()

    return {"thread_id": thread_id}


# -----------------------------
# GET CONVERSATIONS
# -----------------------------
@app.get("/conversations")
def get_conversations():

    cursor.execute("""
        SELECT c.thread_id, m.content
        FROM conversations c
        LEFT JOIN messages m
        ON c.thread_id = m.thread_id
        WHERE m.role='user'
        GROUP BY c.thread_id
        ORDER BY c.rowid DESC
    """)

    rows = cursor.fetchall()

    return [
        {
            "thread_id": r[0],
            "title": r[1][:40] if r[1] else "New Chat"
        }
        for r in rows
    ]


# -----------------------------
# GET CHAT MESSAGES
# -----------------------------
@app.get("/messages/{thread_id}")
def get_messages(thread_id: str):

    cursor.execute(
        "SELECT role,content FROM messages WHERE thread_id=?",
        (thread_id,)
    )

    rows = cursor.fetchall()

    return [
        {"role": r[0], "content": r[1]}
        for r in rows
    ]
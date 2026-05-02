import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.util.protectRoute import get_current_user
from app.schema.user import UserOutput
from app.schema.auth import ChatRequest

from database import conn, cursor

from symptom_agent import symptom_agent_detect, predict_disease_api
from rag_model import knowledge_agent


router = APIRouter()


sessions = {}  


# -----------------------------
# CHAT ENDPOINT
# -----------------------------
@router.post("/chat")
async def chat(
    req: ChatRequest,
    user: UserOutput = Depends(get_current_user)
):

    if len(req.message) > 500:
        return {"response": "Message too long."}

    # CREATE THREAD
    if not req.thread_id:
        req.thread_id = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO conversations(thread_id, user_id) VALUES (%s, %s)",
            (req.thread_id, user.id)
        )
        conn.commit()

    # VERIFY THREAD
    cursor.execute(
        "SELECT user_id FROM conversations WHERE thread_id=%s",
        (req.thread_id,)
    )
    row = cursor.fetchone()

    if not row or row[0] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized thread")

    user_sessions = sessions.setdefault(user.id, {})

    session = user_sessions.setdefault(req.thread_id, {
        "symptoms": [],
        "edit_mode": False
    })

    message = req.message.lower()

    async def generate():

        # ===== YOUR FULL LOGIC (UNCHANGED) =====
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
                    if sym not in symptoms:
                        symptoms.append(sym)

                    response = f"Added symptom: {message}"

        elif session["symptoms"]:

            if message in ["yes", "y"]:

                symptoms = session["symptoms"]

                result = predict_disease_api(symptoms)

                predicted = result["predicted_disease"]

                pred_list = "\n".join(
                    [f"{d} ({round(s*100,2)}%)"
                     for d, s in result["top_predictions"]]
                )

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

                user_sessions.pop(req.thread_id, None)

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

        # SAVE CHAT (POSTGRES FIX)
        cursor.execute(
            "INSERT INTO messages(thread_id,role,content) VALUES (%s,%s,%s)",
            (req.thread_id, "user", req.message)
        )

        cursor.execute(
            "INSERT INTO messages(thread_id,role,content) VALUES (%s,%s,%s)",
            (req.thread_id, "assistant", response)
        )

        conn.commit()

        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.01)

    return StreamingResponse(generate(), media_type="text/plain")


# -----------------------------
# NEW CHAT
# -----------------------------
@router.post("/new_chat")
def new_chat(user: UserOutput = Depends(get_current_user)):

    thread_id = str(uuid.uuid4())

    cursor.execute(
    "INSERT INTO conversations(thread_id, user_id) VALUES (%s, %s)",
    (thread_id, user.id)
)

    conn.commit()

    return {"thread_id": thread_id}


# -----------------------------
# GET CONVERSATIONS
# -----------------------------
@router.get("/conversations")
def get_conversations(user: UserOutput = Depends(get_current_user)):

    cursor.execute("""
    SELECT DISTINCT ON (c.thread_id) c.thread_id, m.content
    FROM conversations c
    LEFT JOIN messages m
    ON c.thread_id = m.thread_id
    WHERE c.user_id = %s AND m.role='user'
    ORDER BY c.thread_id, m.id ASC
""", (user.id,))

    rows = cursor.fetchall()

    return [
        {
            "thread_id": r[0],
            "title": r[1][:40] if r[1] else "New Chat"
        }
        for r in rows
    ]


# -----------------------------
# GET MESSAGES
# -----------------------------
@router.get("/messages/{thread_id}")
def get_messages(thread_id: str, user: UserOutput = Depends(get_current_user)):

    cursor.execute("""
        SELECT m.role, m.content
        FROM messages m
        JOIN conversations c ON m.thread_id = c.thread_id
        WHERE m.thread_id = %s AND c.user_id = %s
    """, (thread_id, user.id))

    rows = cursor.fetchall()

    return [
        {"role": r[0], "content": r[1]}
        for r in rows
    ]
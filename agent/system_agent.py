import pickle
import pandas as pd

from medication_agent import medication_agent
from symptom_agent import symptom_agent_detect, predict_disease_api
from rag_model import knowledge_agent
from symptom_list import symptom_list


# -----------------------------
# Load Drug Database
# -----------------------------
def load_drug_database():

    with open("data/drug_database.pkl", "rb") as f:
        drug_db = pickle.load(f)

    return drug_db


# -----------------------------
# Load Disease Symptoms Dataset
# -----------------------------
def load_disease_symptoms():

    df = pd.read_csv("data/final_Symptom_data.csv")

    return df


# -----------------------------
# Supervisor Agent
# -----------------------------
def supervisor_agent(query, drug_db, disease_symptoms):

    q = query.lower()

    # -----------------------------
    # Medication queries
    # -----------------------------
    drug_keywords = [
        "drug",
        "medicine",
        "dose",
        "dosage",
        "side effect",
        "interaction",
        "tablet",
        "capsule"
    ]

    if any(k in q for k in drug_keywords):

        response = medication_agent(query, drug_db)

        return response


    # -----------------------------
    # Symptom detection
    # -----------------------------
    detect = symptom_agent_detect(query)

    detected_symptoms = detect["symptoms"]


    # -----------------------------
    # If symptoms found → Predict disease
    # -----------------------------
    if detected_symptoms:

        result = predict_disease_api(detected_symptoms)

        predicted = result["predicted_disease"]

        # -----------------------------
        # RAG knowledge retrieval
        # -----------------------------
        rag_answer = knowledge_agent({
            "question": query,
            "predicted_disease": predicted
        })

        response = f"""
Detected Symptoms:
{", ".join(detected_symptoms)}

Predicted Disease: {predicted}

Top Predictions:
{result["top_predictions"]}

Medical Advice:
{rag_answer}
"""

        return response


    # -----------------------------
    # General knowledge query
    # -----------------------------
    rag_answer = knowledge_agent({
        "question": query,
        "predicted_disease": None
    })

    return rag_answer


# -----------------------------
# CLI TEST
# -----------------------------
if __name__ == "__main__":

    print("\nMedical AI Assistant Ready\n")

    drug_db = load_drug_database()
    disease_symptoms = load_disease_symptoms()

    while True:

        query = input("Enter medical query: ")

        if query.lower() in ["exit", "quit"]:
            break

        response = supervisor_agent(
            query,
            drug_db,
            disease_symptoms
        )

        print("\nAnswer:\n")
        print(response)
        print("\n----------------------\n")
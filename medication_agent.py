import pickle
import re
from transformers import pipeline


# -----------------------------
# GLOBAL SUMMARIZER (LAZY LOAD)
# -----------------------------
summarizer = None


def load_summarizer():
    global summarizer

    if summarizer is None:

        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )


# -----------------------------
# LOAD DRUG DATABASE
# -----------------------------
def load_drug_database():

    with open("data/drug_database.pkl", "rb") as f:
        drug_db = pickle.load(f)

    print("Drug database loaded:", len(drug_db), "drugs")

    return drug_db


# -----------------------------
# TEXT CLEANING
# -----------------------------
def clean_text(text):

    if not text or text == "Not available":
        return "Not available"

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -----------------------------
# SUMMARIZATION
# -----------------------------
def summarize_text(text):

    if not text or text == "Not available":
        return "Not available"

    load_summarizer()

    text = clean_text(text)

    text = text[:2000]

    try:

        summary = summarizer(
            text,
            max_length=120,
            min_length=30,
            do_sample=False
        )

        return summary[0]["summary_text"]

    except Exception:

        return text[:300] + "..."


# -----------------------------
# DETECT DRUGS IN QUERY
# -----------------------------
def detect_drugs(query, drug_db):

    query = query.lower()

    detected = []

    for drug in drug_db:

        safe_drug = re.escape(drug)

        if re.search(rf"\b{safe_drug}\b", query):
            detected.append(drug)

    return list(set(detected))


# -----------------------------
# GET DRUG INFORMATION
# -----------------------------
def get_drug_info(drug, drug_db):

    if drug not in drug_db:
        return "Drug not found in database."

    info = drug_db[drug]

    dosage = summarize_text(info.get("dosage"))
    side_effects = summarize_text(info.get("side_effects"))
    contraindications = summarize_text(info.get("contraindications"))
    warnings = summarize_text(info.get("warnings"))

    response = f"""
Drug: {drug}

Dosage:
{dosage}

Side Effects:
{side_effects}

Contraindications:
{contraindications}

Warnings:
{warnings}
"""

    return response


# -----------------------------
# CHECK DRUG INTERACTIONS
# -----------------------------
def check_interaction(drug1, drug2, drug_db):

    text1 = drug_db.get(drug1, {}).get("interactions", "").lower()
    text2 = drug_db.get(drug2, {}).get("interactions", "").lower()

    if re.search(rf"\b{re.escape(drug2)}\b", text1) or re.search(
        rf"\b{re.escape(drug1)}\b", text2
    ):

        return f"""
⚠️ Interaction Risk Detected

{drug1.capitalize()} and {drug2.capitalize()} may interact.

Consult a healthcare professional before combining these medications.
"""

    if text1 == "not available" and text2 == "not available":
        return "Interaction data not available for these drugs."

    return f"No direct interaction found between {drug1} and {drug2}."


# -----------------------------
# MEDICATION AGENT
# -----------------------------
def medication_agent(query, drug_db):

    drugs = detect_drugs(query, drug_db)

    print("Detected drugs:", drugs)

    if len(drugs) == 0:
        return "No drug detected in query."

    if len(drugs) == 1:
        return get_drug_info(drugs[0], drug_db)

    if len(drugs) >= 2:
        return check_interaction(drugs[0], drugs[1], drug_db)


# -----------------------------
# CLI TEST (OPTIONAL)
# -----------------------------
if __name__ == "__main__":

    drug_db = load_drug_database()

    while True:

        query = input("\nAsk about a medicine: ")

        if query.lower() in ["exit", "quit"]:
            break

        response = medication_agent(query, drug_db)

        print("\nResponse:\n", response)
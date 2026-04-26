import os
import re
import json

from symspellpy.symspellpy import SymSpell, Verbosity
from sentence_transformers import SentenceTransformer, util

from symptom_list import symptom_list


# -----------------------------
# CONFIG
# -----------------------------
MAX_EDIT_DISTANCE = 2

LEXICON_FILES = [
    "data/LRWD",
    "data/LRSPL",
    "data/LRAGR"
]

CRITICAL_EMERGENCY = [
    "chest_pain",
    "breathlessness",
    "altered_sensorium",
    "weakness_of_one_body_side",
    "high_fever",
    "bloody_stool",
    "severe_headache"
]

COMMON_ENGLISH = {
'i','have','has','had','am','is','are','was','were','be',
'the','a','an','and','or','but','in','on','at','to','for',
'from','with','by','of','as','very','feel','feeling','felt',
'my','me','you','he','she','it','we','they','do','does',
'did','get','got','make','made','go','went','come','came'
}


# -----------------------------
# LOAD SPECIALIST LEXICON
# -----------------------------
def load_specialist_lexicon():

    vocab = set()

    print("Loading SPECIALIST Lexicon...")

    for file in LEXICON_FILES:

        if not os.path.exists(file):
            print("Missing:", file)
            continue

        with open(file, "r", encoding="utf8", errors="ignore") as f:

            for line in f:

                parts = line.strip().split("|")

                for part in parts:

                    word = part.lower().strip()

                    if word.isalpha() and len(word) > 3:
                        vocab.add(word)

    print("Lexicon words loaded:", len(vocab))

    return vocab


# -----------------------------
# BUILD MEDICAL VOCABULARY
# -----------------------------
def build_medical_vocab():

    vocab = load_specialist_lexicon()

    print("Adding symptom vocabulary...")

    for symptom in symptom_list:
        words = symptom.replace("_", " ").split()
        vocab.update(words)

    print("Adding disease names...")

    try:
        with open("data/combined_disease_symptoms.json") as f:
            diseases = json.load(f)

        for disease in diseases:
            vocab.update(disease.replace("_", " ").split())

    except:
        print("Disease dataset not found")

    print("Final medical vocabulary size:", len(vocab))

    return vocab


# -----------------------------
# TOKENIZER
# -----------------------------
def tokenize(text):

    text = text.lower()

    return re.findall(r"[a-zA-Z]+", text)


# -----------------------------
# WORD CORRECTION
# -----------------------------
def correct_word(word):

    if word in COMMON_ENGLISH:
        return word

    if word in VOCAB:
        return word

    if len(word) < 4:
        return word

    suggestions = SYMSPELL.lookup(word, Verbosity.ALL)

    if not suggestions:
        return word

    best = suggestions[0]

    if best.distance > 2:
        return word

    return best.term


# -----------------------------
# SENTENCE CORRECTION
# -----------------------------
def correct_sentence(sentence):

    tokens = tokenize(sentence)

    corrected = [correct_word(token) for token in tokens]

    return " ".join(corrected)


# -----------------------------
# LOAD MODELS ONCE
# -----------------------------
print("Building medical vocabulary...")

VOCAB = build_medical_vocab()

print("Building SymSpell dictionary...")

SYMSPELL = SymSpell(max_dictionary_edit_distance=MAX_EDIT_DISTANCE)

for word in VOCAB:
    SYMSPELL.create_dictionary_entry(word, 1)


print("Loading symptom embedding model...")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

symptom_texts = [s.replace("_", " ") for s in symptom_list]

symptom_embeddings = embedding_model.encode(symptom_texts, convert_to_tensor=True)


print("Loading disease dataset...")

with open("data/combined_disease_symptoms.json") as f:
    DISEASE_LIST = json.load(f)


# -----------------------------
# SEMANTIC SYMPTOM DETECTION
# -----------------------------
def detect_symptoms_semantic(query, threshold=0.45):

    query_embedding = embedding_model.encode(query, convert_to_tensor=True)

    scores = util.cos_sim(query_embedding, symptom_embeddings)[0]

    detected = []

    for i, score in enumerate(scores):
        if score >= threshold:
            detected.append(symptom_list[i])

    return detected


# -----------------------------
# EMERGENCY CHECK
# -----------------------------
def is_emergency(symptom):

    return symptom in CRITICAL_EMERGENCY


# -----------------------------
# DISEASE PREDICTION
# -----------------------------
def predict_disease(user_symptoms):

    user_symptoms = set(user_symptoms)

    results = []

    for disease, symptoms in DISEASE_LIST.items():

        symptoms = set(symptoms)

        intersection = user_symptoms & symptoms
        union = user_symptoms | symptoms

        score = len(intersection) / len(union)

        if score > 0:
            results.append((disease, score))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:5]


# -----------------------------
# API FUNCTION
# -----------------------------
def symptom_agent_detect(query):

    corrected_query = correct_sentence(query)

    symptoms = detect_symptoms_semantic(corrected_query)

    return {
        "corrected_query": corrected_query,
        "symptoms": symptoms
    }


# -----------------------------
# PREDICTION API
# -----------------------------
def predict_disease_api(symptoms):

    predictions = predict_disease(symptoms)

    predicted = predictions[0][0] if predictions else "Unknown"

    emergency_flag = any(is_emergency(s) for s in symptoms)

    return {
        "predicted_disease": predicted,
        "top_predictions": predictions,
        "emergency": emergency_flag
    }
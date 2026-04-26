import json
import pickle

def build_drug_database(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data["results"]

    drug_db = {}

    for item in records:

        if "openfda" not in item:
            continue

        generic_names = item["openfda"].get("generic_name", [])

        for drug in generic_names:

            drug = drug.lower()

            drug_db[drug] = {
                "dosage": item.get("dosage_and_administration", ["Not available"])[0],
                "side_effects": item.get("adverse_reactions", ["Not available"])[0],
                "contraindications": item.get("contraindications", ["Not available"])[0],
                "warnings": item.get("warnings", ["Not available"])[0],
                "interactions": item.get("drug_interactions", ["Not available"])[0] if "drug_interactions" in item else "Not available"
            }

    return drug_db


# Build database
drug_db = build_drug_database("data\\combined_openfda.json")

# Save it
with open("drug_database.pkl", "wb") as f:
    pickle.dump(drug_db, f)

print("Drug database saved successfully.")
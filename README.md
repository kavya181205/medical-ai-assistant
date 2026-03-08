# 🩺 Medical AI Assistant

An AI-powered medical assistant that helps users identify symptoms, get possible disease predictions, and receive medication guidance through a conversational chatbot interface.

This project integrates **Natural Language Processing (NLP), medical knowledge bases, and AI agents** to provide intelligent healthcare support.

⚠️ **Disclaimer:** This project is for educational and research purposes only. It should not be used as a substitute for professional medical advice.

---

# 🚀 Features

- 🧠 **Symptom Detection Agent**
  - Extracts symptoms from user queries using NLP techniques.

- 🦠 **Disease Prediction**
  - Predicts possible diseases based on detected symptoms.

- 💊 **Medication Recommendation**
  - Suggests possible medications and treatments.

- 🤖 **Multi-Agent AI Architecture**
  - Symptom Agent
  - Disease Prediction Agent
  - Medication Agent
  - Supervisor Agent

- 💬 **Conversational Chat Interface**
  - Users interact with the system using natural language.

- 🗂 **Conversation History**
  - Maintains chat history for better context handling.

- ⚡ **FastAPI Backend**
  - High-performance API for AI-powered medical queries.

---

# 🏗 System Architecture
```
User Query
│
▼
Supervisor Agent
│
├── Symptom Detection Agent
│
├── Disease Prediction Agent
│
└── Medication Recommendation Agent
│
▼
Response Generation
│
▼
Chat Interface
```

---

# 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Core programming language |
| FastAPI | Backend API framework |
| NLP | Symptom extraction and query understanding |
| Machine Learning | Disease prediction |
| JSON Medical Dataset | Symptom-disease mapping |

---

# 📂 Project Structure
```
medical-ai-assistant
│
├── data/
│ ├── disease_symptoms.json
│ ├── drug_database.json
│
├── agents/
│ ├── symptom_agent.py
│ ├── disease_agent.py
│ ├── medication_agent.py
│
├── system_agent.py
├── database.py
├── main.py
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```
git clone https://github.com/kavya181205/medical-ai-assistant.git
cd medical-ai-assistant
```
2️⃣ Create Virtual Environment
``` 
python -m venv venv
 ```

Activate environment

Windows

``` 
venv\Scripts\activate
```

Linux / Mac

source venv/bin/activate
3️⃣ Install Dependencies
``` 
pip install -r requirements.txt
 ```
▶️ Run the Application

Start the FastAPI server

```
uvicorn main:app --reload
``` 

Server will start at

```
http://127.0.0.1:8000
 ```

API Docs

```
http://127.0.0.1:8000/docs
 ```

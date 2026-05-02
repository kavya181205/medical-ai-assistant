import os
import psycopg2
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV VARIABLES
# -----------------------------
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# -----------------------------
# CONNECT TO POSTGRES
# -----------------------------
conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=DB_PORT
)

cursor = conn.cursor()

print("✅ Connected to PostgreSQL")

# -----------------------------
# CREATE TABLES
# -----------------------------
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        thread_id TEXT UNIQUE,
        user_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        thread_id TEXT,
        role TEXT,
        content TEXT
    )
    """)

    conn.commit()
    print("✅ Tables created successfully")

# Run once on startup
create_tables()
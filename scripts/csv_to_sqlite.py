import sqlite3
import pandas as pd
import os

# --- CONFIGURATION ---
CSV_FILE = "MOST_final_merged_dataset.csv"
DB_FILE = "db.sqlite3"

def load_data():
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found.")
        return

    print(f"📖 Reading {CSV_FILE}...")
    # Load CSV (skipping bad lines to prevent crashes)
    try:
        df = pd.read_csv(CSV_FILE, encoding="latin-1", on_bad_lines='skip')
    except:
        df = pd.read_csv(CSV_FILE, on_bad_lines='skip')

    print(f"💾 Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create table with ALL columns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        Acc_Date TEXT,
        Acc_No INTEGER PRIMARY KEY,
        Title TEXT,
        ISBN TEXT,
        Author_Editor TEXT,
        Edition_Volume TEXT,
        Place_Publisher TEXT,
        Year INTEGER,
        Pages TEXT,
        Class_No TEXT,
        description TEXT
    )
    """)
    
    print(" Inserting rows...")
    
    for _, row in df.iterrows():
        # Clean specific fields to match types (Integer/String)
        try:
            acc_no = int(row["Acc_No"])
        except:
            continue # Skip row if Acc_No is invalid

        try:
            year = int(row["Year"]) if pd.notna(row["Year"]) else None
        except:
            year = None

        cursor.execute("""
        INSERT OR IGNORE INTO books
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["Acc_Date"],
            acc_no,
            row["Title"],
            str(row["ISBN"]),
            row["Author_Editor"],
            row["Edition_Volume"],
            row["Place_Publisher"],
            year,
            row["Pages"],
            row["Class_No"],
            row["description"]
        ))

    conn.commit()
    conn.close()

    print(f"✅ FULL CSV copied into SQLite ({DB_FILE})")

if __name__ == "__main__":
    load_data()
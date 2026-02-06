from fastapi import FastAPI, HTTPException, Query, Depends
from contextlib import asynccontextmanager
import sqlite3
import pandas as pd
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

# --- CONFIGURATION ---
DB_PATH = "data\db.sqlite3"
CSV_SOURCE = "data\processed\Final_Merged_Dataset.csv"
VECTORS_PATH = "books_vectors.pkl"
MODEL_NAME = 'all-MiniLM-L6-v2'

# --- GLOBAL VARIABLES (The AI Brain) ---
# These sit in RAM so they are fast to access
ai_model = None
book_vectors = None
book_df = None

# --- LIFESPAN MANAGER (Starts when you run uvicorn) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_model, book_vectors, book_df
    
    print("⏳ Starting up... Loading AI Model & Vectors...")
    
    try:
        # 1. Load the Sentence Transformer
        ai_model = SentenceTransformer(MODEL_NAME)
        
        # 2. Load the Pickle File (Vectors)
        if os.path.exists(VECTORS_PATH):
            with open(VECTORS_PATH, "rb") as f:
                data = pickle.load(f)
                book_df = data["dataframe"]
                book_vectors = data["embeddings"]
            print("✅ AI System Ready! /recommend endpoint is active.")
        else:
            print("⚠️ Warning: books_vectors.pkl not found. Run generate_embeddings.py first.")
            
    except Exception as e:
        print(f"❌ Error loading AI: {e}")
        
    yield  # The application runs here
    
    # Clean up when server stops
    print("🛑 Server shutting down...")
    del ai_model
    del book_vectors

app = FastAPI(
    title="Book Library AI API",
    description="Phase 2: Hybrid Search (SQL) + Semantic Recommendation (AI)",
    version="2.0.0",
    lifespan=lifespan
)

# -----------------------------
# Dependency: Database Session
# -----------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# -----------------------------
# 1. Health Check
# -----------------------------
@app.get("/")
def root():
    ai_status = "active" if ai_model is not None else "inactive"
    return {"status": "online", "ai_engine": ai_status}

# -----------------------------
# 2. Get Books (SQL Pagination)
# -----------------------------
@app.get("/books")
def get_books(limit: int = 20, offset: int = 0, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books LIMIT ? OFFSET ?", (limit, offset))
    rows = [dict(row) for row in cursor.fetchall()]
    return {"count": len(rows), "data": rows}

# -----------------------------
# 3. Keyword Search (SQL LIKE)
# -----------------------------
@app.get("/search")
def search_books(q: str = Query(..., min_length=3), db: sqlite3.Connection = Depends(get_db)):
    """Standard text search for Title or Author."""
    cursor = db.cursor()
    search_term = f"%{q}%"
    cursor.execute("""
        SELECT * FROM books 
        WHERE title LIKE ? OR author_editor LIKE ?
        LIMIT 20
    """, (search_term, search_term))
    rows = [dict(row) for row in cursor.fetchall()]
    return {"query": q, "matches": len(rows), "results": rows}

# -----------------------------
# 4. AI Recommendation (Semantic Search)
# -----------------------------
@app.post("/recommend")
def recommend_books(user_query: str):
    """
    Input: "I want a sad story about space travel"
    Output: Top 5 books that match the MEANING (vectors).
    """
    if ai_model is None or book_vectors is None:
        raise HTTPException(status_code=503, detail="AI System is not loaded.")

    # 1. Convert User Query to Vector
    query_vector = ai_model.encode([user_query])
    
    # 2. Calculate Similarity (Dot Product)
    scores = np.dot(book_vectors, query_vector.T).flatten()
    
    # 3. Get Top 5 Indices
    top_indices = np.argsort(scores)[-5:][::-1]
    
    # 4. Retrieve Book Details from DataFrame (Fast RAM lookup)
    results = []
    for idx in top_indices:
        book = book_df.iloc[idx]
        results.append({
            "title": str(book['Title']),
            "author": str(book['Author_Editor']),
            "description": str(book['description'])[:200] + "...", # Truncate for clean display
            "score": float(f"{scores[idx]:.4f}")
        })
        
    return {"query": user_query, "recommendations": results}

# -----------------------------
# 5. Get Book by ISBN
# -----------------------------
@app.get("/books/{isbn}")
def get_book_by_isbn(isbn: str, db: sqlite3.Connection = Depends(get_db)):
    clean_isbn = isbn.strip().replace("-", "")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books WHERE REPLACE(isbn, '-', '') = ?", (clean_isbn,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return dict(row)

# -----------------------------
# 6. Sync Data (Reset DB)
# -----------------------------
@app.post("/sync")
def sync_database():
    if not os.path.exists(CSV_SOURCE):
        raise HTTPException(status_code=500, detail="Source CSV not found")
    try:
        df = pd.read_csv(CSV_SOURCE, encoding="latin-1", on_bad_lines='skip')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS books")
        cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acc_no TEXT,
            title TEXT,
            isbn TEXT,
            author_editor TEXT,
            publisher TEXT,
            year INTEGER,
            pages INTEGER,
            class_no TEXT,
            description TEXT
        )
        """)
        df.columns = [c.strip().lower() for c in df.columns]
        df.to_sql("books", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Synced {len(df)} books."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# from fastapi import FastAPI, HTTPException, Query, Depends
# import sqlite3
# import pandas as pd
# import os
# from typing import List, Dict, Any

# # --- CONFIGURATION ---
# DB_PATH = "db.sqlite3"
# CSV_SOURCE = "data/processed/dau_with_description.csv"

# app = FastAPI(
#     title="Book Library API",
#     description="Professional API with Search, Sync, and ISBN cleaning.",
#     version="2.0.0"
# )

# # -----------------------------
# # Dependency: Database Session
# # -----------------------------
# def get_db():
#     """Opens a connection, yields it to the endpoint, then closes it."""
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row  # Access columns by name
#     try:
#         yield conn
#     finally:
#         conn.close()

# # -----------------------------
# # 1. Health Check
# # -----------------------------
# @app.get("/")
# def root():
#     return {"status": "online", "message": "Library API v2 is running"}

# # -----------------------------
# # 2. Get Books (Pagination)
# # -----------------------------
# @app.get("/books")
# def get_books(
#     limit: int = Query(20, ge=1, le=100),
#     offset: int = 0,
#     db: sqlite3.Connection = Depends(get_db)
# ):
#     cursor = db.cursor()
#     cursor.execute("SELECT * FROM books LIMIT ? OFFSET ?", (limit, offset))
#     rows = [dict(row) for row in cursor.fetchall()]
#     return {"count": len(rows), "data": rows}

# # -----------------------------
# # 3. Search (Title/Author/Desc)
# # -----------------------------
# @app.get("/search")
# def search_books(
#     q: str = Query(..., min_length=3, description="Search query"),
#     db: sqlite3.Connection = Depends(get_db)
# ):
#     cursor = db.cursor()
#     search_term = f"%{q}%"
    
#     # Searches Title, Author, OR Description
#     cursor.execute("""
#         SELECT * FROM books 
#         WHERE title LIKE ? OR author_editor LIKE ? OR description LIKE ?
#         LIMIT 20
#     """, (search_term, search_term, search_term))
    
#     rows = [dict(row) for row in cursor.fetchall()]
#     return {"query": q, "matches": len(rows), "results": rows}

# # -----------------------------
# # 4. Get Book by ISBN (Unified)
# # -----------------------------
# def query_book_by_isbn(isbn: str, db: sqlite3.Connection) -> Dict[str, Any]:
#     # Remove dashes for cleaner matching (e.g. 978-1-23 -> 978123)
#     clean_isbn = isbn.strip().replace("-", "")
#     cursor = db.cursor()
    
#     # We strip dashes from the database column dynamically too
#     cursor.execute("""
#         SELECT * FROM books
#         WHERE REPLACE(isbn, '-', '') = ?
#     """, (clean_isbn,))
    
#     row = cursor.fetchone()
#     if row is None:
#         raise HTTPException(status_code=404, detail="Book not found")
#     return dict(row)

# @app.get("/books/{isbn}")
# def get_book_path(isbn: str, db: sqlite3.Connection = Depends(get_db)):
#     return query_book_by_isbn(isbn, db)

# # -----------------------------
# # 5. The SYNC Endpoint
# # -----------------------------
# @app.post("/sync")
# def sync_database():
#     """Wipes the DB and reloads from CSV."""
#     if not os.path.exists(CSV_SOURCE):
#         raise HTTPException(status_code=500, detail="Source CSV not found")
    
#     try:
#         # 1. Read CSV
#         df = pd.read_csv(CSV_SOURCE, encoding="latin-1", on_bad_lines='skip')
        
#         # 2. Connect (Manually, because this function does bulk work)
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()
        
#         # 3. Re-create Table
#         cursor.execute("DROP TABLE IF EXISTS books")
#         cursor.execute("""
#         CREATE TABLE books (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             acc_no TEXT,
#             title TEXT,
#             isbn TEXT,
#             author_editor TEXT,
#             publisher TEXT,
#             year INTEGER,
#             pages INTEGER,
#             class_no TEXT,
#             description TEXT
#         )
#         """)
        
#         # 4. Insert Data
#         # Ensure your CSV columns match these headers!
#         # If your CSV has 'Acc_No', rename it to 'acc_no' here if needed:
#         df.columns = [c.strip().lower() for c in df.columns]
        
#         # Save to SQL
#         df.to_sql("books", conn, if_exists="append", index=False)
        
#         count = len(df)
#         conn.commit()
#         conn.close()
        
#         return {"status": "success", "message": f"Synced {count} books."}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Sync Error: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
# from fastapi import FastAPI, HTTPException, Query, Depends
# import sqlite3
# from typing import List, Dict, Any

# app = FastAPI(
#     title="Book Library API",
#     description="API to fetch cleaned book data from SQLite",
#     version="1.0.0"
# )

# DB_PATH = "db.sqlite3"

# # -----------------------------
# # Dependency: Database Session
# # -----------------------------
# def get_db():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     try:
#         yield conn
#     finally:
#         conn.close()

# # -----------------------------
# # Health Check
# # -----------------------------
# @app.get("/")
# def root():
#     return {"message": "Book Library API is working"}

# # -----------------------------
# # Get Latest Books
# # -----------------------------
# @app.get("/books")
# def get_books(
#     limit: int = Query(1000, ge=1, le=5000),
#     db: sqlite3.Connection = Depends(get_db)
# ):
#     cursor = db.cursor()
#     cursor.execute("""
#         SELECT *
#         FROM books
#         WHERE description IS NOT NULL
#         ORDER BY Acc_Date DESC
#         LIMIT ?
#     """, (limit,))
    
#     books = [dict(row) for row in cursor.fetchall()]
#     return {"count": len(books), "data": books}

# # -----------------------------
# # Get Book by ISBN (Unified Logic)
# # -----------------------------
# def query_book_by_isbn(isbn: str, db: sqlite3.Connection) -> Dict[str, Any]:
#     """Helper function to avoid repeating SQL logic."""
#     clean_isbn = isbn.strip().replace("-", "")
#     cursor = db.cursor()
#     cursor.execute("""
#         SELECT *
#         FROM books
#         WHERE REPLACE(ISBN, '-', '') = ?
#     """, (clean_isbn,))
    
#     row = cursor.fetchone()
#     if row is None:
#         raise HTTPException(status_code=404, detail="Book not found")
#     return dict(row)

# @app.get("/book")
# def get_book_by_isbn_query(
#     isbn: str = Query(..., description="ISBN number"),
#     db: sqlite3.Connection = Depends(get_db)
# ):
#     return query_book_by_isbn(isbn, db)

# @app.get("/books/{isbn}")
# def get_book_by_isbn_path(
#     isbn: str, 
#     db: sqlite3.Connection = Depends(get_db)
# ):
#     return query_book_by_isbn(isbn, db)


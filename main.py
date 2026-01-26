from fastapi import FastAPI, HTTPException, Query, Depends
import sqlite3
from typing import List, Dict, Any

app = FastAPI(
    title="Book Library API",
    description="API to fetch cleaned book data from SQLite",
    version="1.0.0"
)

DB_PATH = "db.sqlite3"

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
# Health Check
# -----------------------------
@app.get("/")
def root():
    return {"message": "Book Library API is working"}

# -----------------------------
# Get Latest Books
# -----------------------------
@app.get("/books")
def get_books(
    limit: int = Query(1000, ge=1, le=5000),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("""
        SELECT *
        FROM books
        WHERE description IS NOT NULL
        ORDER BY Acc_Date DESC
        LIMIT ?
    """, (limit,))
    
    books = [dict(row) for row in cursor.fetchall()]
    return {"count": len(books), "data": books}

# -----------------------------
# Get Book by ISBN (Unified Logic)
# -----------------------------
def query_book_by_isbn(isbn: str, db: sqlite3.Connection) -> Dict[str, Any]:
    """Helper function to avoid repeating SQL logic."""
    clean_isbn = isbn.strip().replace("-", "")
    cursor = db.cursor()
    cursor.execute("""
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """, (clean_isbn,))
    
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return dict(row)

@app.get("/book")
def get_book_by_isbn_query(
    isbn: str = Query(..., description="ISBN number"),
    db: sqlite3.Connection = Depends(get_db)
):
    return query_book_by_isbn(isbn, db)

@app.get("/books/{isbn}")
def get_book_by_isbn_path(
    isbn: str, 
    db: sqlite3.Connection = Depends(get_db)
):
    return query_book_by_isbn(isbn, db)


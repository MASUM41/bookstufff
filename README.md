# 📚 Book Description Enrichment Pipeline
### Big Data Engineering Mini Project

A comprehensive data engineering pipeline to enrich library book records with missing descriptions using multiple public data sources, followed by structured storage in SQLite and API-based access via FastAPI.

---

## 📑 Table of Contents
- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Data Sources](#-data-sources)
- [Dataset Evolution](#-dataset-evolution)
- [Final Data Schema](#-final-data-schema)
- [Database Design](#-database-design)
- [API Endpoints](#-api-endpoints-fastapi)
- [Technologies Used](#-technologies-used)

---

## 📌 Overview
This project implements an **end-to-end data enrichment pipeline** that:
- Starts from a raw library dataset with **no book descriptions**.
- Collects missing descriptions from **multiple external sources**.
- Applies **multi-stage fallback logic** to maximize coverage.
- Cleans and merges data into a **final unified dataset**.
- Stores enriched data in **SQLite**.
- Serves data using **FastAPI REST endpoints**.

This project reflects **real-world data engineering challenges**, especially for **Indian publications**, where book descriptions are often unavailable from a single source.

---

## ❓ Problem Statement
The original dataset (`dau_library.csv`) did not contain a book description column. Additionally:
- **OpenLibrary** provides limited coverage for Indian books.
- **ISBN-based lookups** frequently fail for older or local editions.
- A **single data source** was insufficient to achieve high coverage.

**Solution:** A **multi-source enrichment and fallback strategy** was designed to iteratively fill gaps.

---

## 🧩 Data Sources
1.  **Local Library Dataset (CSV)**: The raw metadata.
2.  **OpenLibrary API**: Used for initial ISBN-based lookups.
3.  **Google Books**:
    - **HTML Scraping**: Extracted descriptions directly from web pages.
    - **API Fallback**: Used for fuzzy searching.
    - **Title + Author Search**: Used when ISBNs failed.

---

## 🗂 Dataset Evolution

### 1️⃣ Base Dataset (No Descriptions)
**File:** `dau_library.csv`
- **Contains:** Accession Date, Acc No, Title, ISBN, Author/Editor, Publisher, Year, Pages, Class No.
- **Status:** ❌ No description column.

### 2️⃣ ISBN-Based Description Fetch (OpenLibrary)
**File:** `OpenLibrary_5000.csv`
- **Action:** Selected the first **5,000 records** and queried the OpenLibrary API.
- **Result:** Partial success; many returned `"Not Found"`.

### 3️⃣ Google Books HTML Scraping (Large Scale)
**File:** `HTML_tag_through_All_36000.csv`
- **Action:** Scraped ~36,000 book pages on Google Books using ISBNs.
- **Technique:** Parsed HTML tags to extract the synopsis.
- **Result:** Higher coverage than OpenLibrary, but gaps remained.

### 4️⃣ First Merge (Google Books + OpenLibrary)
**File:** `Final_Merged_Descriptions.csv`
- **Logic:**
    - **Primary Source:** Google Books.
    - **Fallback Source:** OpenLibrary.
    - *If Google Books description is missing, fill using OpenLibrary.*
- **Result:** Significant reduction in missing descriptions.

### 5️⃣ Title + Author Based Fetch (Final Fallback)
**File:** `Final_GoogleBooks_Descriptions.csv`
- **Action:** Filtered remaining `"Not Found"` rows.
- **Technique:** Performed a **Title + Author** search (fuzzy matching) instead of strict ISBN matching.
- **Cleaning:** Text was lowercased and punctuation removed for better matching.
- **Result:** Recovered descriptions for books with bad/missing ISBNs.

### 6️⃣ Final Clean Dataset
**File:** `dau_with_description.csv`
- **Action:** Merged the results from Step 4 and Step 5.
- **Status:** ✅ Ready for SQLite database insertion.

---

## 🧾 Final Data Schema

| Column Name | Description |
| :--- | :--- |
| `acc_no` | Unique Accession number (Primary Key) |
| `title` | Book title |
| `isbn` | ISBN number |
| `author_editor` | Author / Editor name |
| `publisher` | Publisher details |
| `year` | Publication year |
| `pages` | Number of pages |
| `class_no` | Classification number |
| `description` | **Enriched book description** (The target feature) |

---

## 🗄 Database Design
**Database:** `library.db` (SQLite)

```sql
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
);
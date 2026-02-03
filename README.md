# Big Data Engineering Project Workflow

## Project Overview
This project is a **Book Library Data Pipeline** that fetches book descriptions from multiple sources (OpenLibrary, Google Books, Wikipedia), stores them in a SQLite database, and exposes the data through a professional FastAPI REST API.

---

## Architecture & Workflow

### 1. **Data Collection & Enrichment** (`Data-Building/`)

#### Input
- **Source**: `dau_library_data.csv` - Raw library data with book metadata
  - Columns: Acc_Date, Acc_No, Title, ISBN, Author_Editor, Edition_Volume, Place_Publisher, Year, Pages, Class_No

#### Processing: `fetch_description.py` & `rescue_script.py`
The pipeline enriches raw data by fetching descriptions using a **multi-stage fallback strategy**.

**Steps:**
1. **Load & Clean Data**
   - Read CSV file (encoding: latin1)
   - Remove duplicate records based on Title, ISBN, and Author.
   - Initialize description column with "Not Found".

2. **Fetch from OpenLibrary** (First Priority)
   - Query: `https://openlibrary.org/isbn/{ISBN}`
   - Extract description via HTML scraping.
   - Rate limit: 1 second delay per request.

3. **Fetch from Google Books** (Second Priority - Scraper)
   - For missing descriptions, query: `https://books.google.com/books?vid=ISBN{ISBN}`
   - Scrape synopsis from `<div id="synopsis">`.

4. **Fetch from Google Books API** (Third Priority - Fuzzy Search)
   - If ISBN fails, search by **Title + Author** using the Google Books API.
   - Handles invalid ISBNs effectively.

5. **Fetch from Wikipedia** (Final Rescue - API)
   - **New Feature:** For stubborn records, utilize the `wikipedia` Python library.
   - Search query: `"{Title} (novel)"` to find book summaries.
   - Fills remaining gaps to ensure maximum data coverage.

#### Output
- **File**: `Data/processed/dau_with_description.csv`
- Contains all original columns + new `description` column.

---

### 2. **Data Statistics (Enrichment Results)**

Our multi-stage pipeline achieved significant data enrichment coverage.

| Stage | Action | Result |
| :--- | :--- | :--- |
| **1. Input** | Initial Raw Data | **36,000** Total Rows |
| **2. OpenLibrary** | Attempted on first 5,000 rows | Found **~3,500** descriptions |
| **3. Google Books** | Merged OpenLibrary + Google Books results | **9,000** rows still "Not Found" (25% gap) |
| **4. Wikipedia** | Applied Rescue Script on "Not Found" rows | Recovered thousands of missing descriptions |
| **5. Final Output** | **Final Enriched Dataset** | **30,400** Books with Descriptions (84% Coverage) |

---

### 3. **Database Setup** (`Database/`)

#### Script: `SQLite3.py` (Manual) or `/sync` Endpoint (Automated)
Loads the enriched CSV data into SQLite3 database.

**Schema:**
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acc_no TEXT,
    title TEXT,
    isbn TEXT,
    author_editor TEXT,
    description TEXT,
    ...
);

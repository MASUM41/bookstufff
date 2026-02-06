import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import os

# --- CONFIGURATION ---
CSV_PATH = r"C:\Desktop\new desk\gamelecturenotes\BIG_DATA_PROJECT\data\processed\Final_Merged_Dataset.csv"
OUTPUT_PKL_PATH = "books_vectors.pkl"
MODEL_NAME = 'all-MiniLM-L6-v2'

def generate_vectors():
    # 1. Load the Data
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: Could not find {CSV_PATH}")
        return

    print(f"📖 Reading CSV from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, encoding="latin-1", on_bad_lines='skip')
    
    # 2. Data Cleaning (Crucial for AI)
    # Fill empty descriptions with blank strings so the AI doesn't crash
    df['description'] = df['description'].fillna("Description not available")
    df['Title'] = df['Title'].fillna("Unknown Title")
    df['Author_Editor'] = df['Author_Editor'].fillna("Unknown Author")

    print(f"✅ Loaded {len(df)} books.")

    # 3. Create "Combined Text" for better search
    # We combine Title + Author + Description so the AI understands context better.
    # Example: "Harry Potter J.K. Rowling A wizard boy goes to school..."
    print("🔄 Combining text columns...")
    df['combined_text'] = (
        df['Title'].astype(str) + " " + 
        df['Author_Editor'].astype(str) + " " + 
        df['description'].astype(str)
    )

    # 4. Load the AI Model
    print(f"⏳ Loading AI Model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)

    # 5. Generate Embeddings (The Heavy Lifting)
    print("🧠 Generating Vectors... (This typically takes 2-10 minutes)")
    # We convert the list of text strings into a Matrix of numbers
    embeddings = model.encode(df['combined_text'].tolist(), show_progress_bar=True)

    print(f"✅ Created Matrix of shape: {embeddings.shape}")
    # Shape should be (30400, 384)

    # 6. Save to Pickle (The "Brain" File)
    print(f"💾 Saving to {OUTPUT_PKL_PATH}...")
    
    data_to_save = {
        "dataframe": df,        # We save the text data
        "embeddings": embeddings # AND the number matrix together
    }

    with open(OUTPUT_PKL_PATH, "wb") as f:
        pickle.dump(data_to_save, f)

    print("🎉 Success! You can now restart your API.")

if __name__ == "__main__":
    generate_vectors()
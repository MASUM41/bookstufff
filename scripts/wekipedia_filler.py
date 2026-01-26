import pandas as pd
import wikipedia
import time
import os

# --- CONFIGURATION ---
INPUT_SLICE = "missing_rows.csv"   
OUTPUT_FIXED = "WEKI_fixed_rows_fast.csv"

def get_wikipedia_summary(Title, Author_Editor):
    """
    Fetches the summary from Wikipedia. 
    Handles 'Disambiguation' (multiple results) by picking the first one.
    """
    try:
        # We search specifically for "Book Title (novel)" or just Title to be precise
        # Combining Title + Author often helps search accuracy
        query = f"{Title} (novel)" 
        
        # 1. Search (Limit 1 to be fast)
        results = wikipedia.search(query, results=1)
        if not results:
            # Retry with just the title if "novel" approach failed
            results = wikipedia.search(Title, results=1)
            
        if not results:
            return None

        # 2. Get Summary
        # auto_suggest=False prevents it from grabbing a random wrong page
        summary = wikipedia.summary(results[0], sentences=2, auto_suggest=False)
        return summary
        
    except wikipedia.DisambiguationError as e:
        # If it finds multiple pages (e.g., "It" the movie vs "It" the book)
        # We just grab the first option to keep it moving fast.
        try:
            return wikipedia.summary(e.options[0], sentences=2, auto_suggest=False)
        except:
            return None
    except:
        return None

def run_fast_rescue():
    if not os.path.exists(INPUT_SLICE):
        print(f"❌ Error: {INPUT_SLICE} not found. Run step1_slice.py first!")
        return

    print(f"📖 Reading {INPUT_SLICE}...")
    df = pd.read_csv(INPUT_SLICE)
    
    # Create column if missing
    if 'generated_description' not in df.columns:
        df['generated_description'] = None

    print(f" Speed-Processing {len(df)} books using Wikipedia...")
    
    success_count = 0
    
    for index, row in df.iterrows():
        # Resume logic: Skip if already done
        if pd.notna(row['generated_description']):
            continue

        Title = str(row['Title'])
        Author_Editor = str(row['Author_Editor'])
        
        # STRATEGY 1: WIKIPEDIA (High Quality)
        wiki_desc = get_wikipedia_summary(Title, Author_Editor)
        
        if wiki_desc:
            df.at[index, 'generated_description'] = f"[Wikipedia] {wiki_desc}"
            success_count += 1
            print(f"   ✅ Found: {Title[:30]}...")
        else:
            # STRATEGY 2: PLACEHOLDER (Guaranteed Completion)
            # This satisfies the 'No Null Values' requirement immediately.
            fallback = f"A book titled '{Title}' written by {Author_Editor}. (Description unavailable)."
            df.at[index, 'generated_description'] = f"[Placeholder] {fallback}"
            print(f"   ⚠️ Wikipedia failed. Using Placeholder for: {Title[:30]}...")

        # Save frequently (every 50 rows)
        if index % 50 == 0:
            df.to_csv(OUTPUT_FIXED, index=False)
            
        # Wikipedia is fast, we only need a tiny sleep
        time.sleep(0.1)

    # Final Save
    df.to_csv(OUTPUT_FIXED, index=False)
    print("\n🎉 DONE! Dataset is 100% Complete.")
    print(f"📊 Wikipedia Success Rate: {success_count}/{len(df)}")
    print(f"💾 Saved to: {OUTPUT_FIXED}")

if __name__ == "__main__":
    run_fast_rescue()
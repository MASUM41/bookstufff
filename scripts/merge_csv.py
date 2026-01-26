import pandas as pd

# 1. Load the CSV files
df_main = pd.read_csv('Final_Merged_Descriptions (6).csv')
df_wiki = pd.read_csv('final_WEKI_fixed_rows_fast.csv')
# df_wiki = pd.read_csv('missing_rows.csv')
# --- DATA CLEANING (Recommended) ---
# Ensure ISBNs and Titles are strings and strip whitespace to maximize matches
df_main['ISBN'] = df_main['ISBN'].astype(str).str.strip()
df_wiki['ISBN'] = df_wiki['ISBN'].astype(str).str.strip()
df_main['Title'] = df_main['Title'].astype(str).str.strip()
df_wiki['Title'] = df_wiki['Title'].astype(str).str.strip()

# --- PREPARE LOOKUP TABLES ---
# We drop duplicates in the wiki file to prevent your main dataset 
# from expanding (creating extra rows) during the merge.
wiki_ISBN_lookup = df_wiki[['ISBN', 'description']].drop_duplicates(subset='ISBN')
wiki_title_lookup = df_wiki[['Title', 'description']].drop_duplicates(subset='Title')

# --- STEP 1: MERGE ON ISBN ---
# Left join ensures we keep all rows from your main file
merged_df = pd.merge(df_main, wiki_ISBN_lookup, on='ISBN', how='left')

# --- STEP 2: FILL MISSING VALUES WITH TITLE MATCH ---
# We map the titles to descriptions and fill ONLY where the 'description' is currently NaN
title_description_map = wiki_title_lookup.set_index('Title')['description']
merged_df['description'] = merged_df['description'].fillna(merged_df['Title'].map(title_description_map))

# --- SAVE RESULT ---
merged_df.to_csv('Final_Merged_Descriptions (6).csv', index=False)

print("Merge complete. Saved to 'main_with_descriptions.csv'")
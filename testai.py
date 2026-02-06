import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Load the AI Model
print("⏳ Loading Model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Load the Pickle file (The AI Brain)
print("⏳ Loading Vectors...")
with open("books_vectors.pkl", "rb") as f:
    data = pickle.load(f)
    book_df = data["dataframe"]
    book_vectors = data["embeddings"]

def test_recommendation(query):
    print(f"\n🔍 Searching for: '{query}'")
    
    # AI step: Convert query to numbers
    query_vec = model.encode([query])
    
    # Math step: Dot Product (Similarity)
    scores = np.dot(book_vectors, query_vec.T).flatten()
    
    # Logic step: Get Top 3 matches
    top_indices = np.argsort(scores)[-3:][::-1]
    
    print("-" * 30)
    for idx in top_indices:
        title = book_df.iloc[idx]['Title'] # Note: Using 'Title' from your DF
        author = book_df.iloc[idx]['Author_Editor']
        score = scores[idx]
        print(f"📚 {title} by {author}")
        print(f"   (Match Score: {score:.4f})")
    print("-" * 30)

# 3. RUN TESTS
test_recommendation("A story about space and stars")
test_recommendation("Kafkaesque dark psychology")
test_recommendation("Linear algebra and optimization")
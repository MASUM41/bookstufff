import streamlit as st
import requests

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"

# --- PAGE SETUP ---
st.set_page_config(page_title="Library AI", page_icon="📚", layout="wide")

st.title("Intelligent Library Search")
st.markdown("### Powered by Hybrid Search (SQL + Vector AI)")

# --- SIDEBAR ---
st.sidebar.header("Search Options")
search_mode = st.sidebar.radio("Select Mode:", ["AI Recommendation (Semantic)", "🔍 Database Search (Keyword)"])

# --- MAIN LOGIC ---
if search_mode == "AI Recommendation (Semantic)":
    st.subheader("Find books by Concept, Vibe, or Plot")
    query = st.text_input("Describe what you want to read:", placeholder="e.g., 'A sad story about space travel' or 'Introduction to linear algebra'")
    
    if st.button("Ask AI"):
        if query:
            with st.spinner("AI is thinking..."):
                try:
                    # Call your /recommend endpoint
                    response = requests.post(f"{API_URL}/recommend", params={"user_query": query})
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("recommendations", [])
                        
                        if not results:
                            st.warning("No matches found.")
                        
                        # Display Results in a Grid
                        for book in results:
                            with st.container():
                                st.markdown("---")
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.metric(label="Match Score", value=f"{float(book['score'])*100:.1f}%")
                                with col2:
                                    st.markdown(f"### 📖 {book['title']}")
                                    st.markdown(f"**Author:** {book['author']}")
                                    st.info(book['description'])
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

elif search_mode == "Database Search (Keyword)":
    st.subheader("Search by Exact Title or Author")
    query = st.text_input("Enter keywords:", placeholder="e.g., 'Harry Potter' or 'Sagan'")
    
    if st.button("Search Database"):
        if query:
            with st.spinner("Searching SQL Database..."):
                try:
                    response = requests.get(f"{API_URL}/search", params={"q": query})
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        
                        st.success(f"Found {data['matches']} matches.")
                        
                        for book in results:
                            with st.expander(f"📘 {book['Title']} - {book['Author_Editor']}"):
                                st.write(f"**ISBN:** {book['ISBN']}")
                                st.write(f"**Year:** {book['Year']}")
                                st.write(f"**Description:** {book['description']}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
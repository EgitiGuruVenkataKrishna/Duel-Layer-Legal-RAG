import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1/query"

st.set_page_config(page_title="Indian Legal RAG", page_icon="⚖️", layout="centered")

st.title("⚖️ Zero-Hallucination Legal RAG")
st.markdown("Powered by **Dual-Tier LangGraph Architecture** & **Groq Llama 3.1**")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_query = st.chat_input("Ask a legal question regarding BNS, BNSS, BSA, etc...")

if user_query:
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
        
    with st.chat_message("assistant"):
        with st.spinner("Analyzing legal frameworks..."):
            try:
                response = requests.post(API_URL, json={"query": user_query})
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display metadata badges
                    tier_badge = "🟢 Tier 1 (Direct)" if data["tier"] == "tier1" else "🟣 Tier 2 (Scenario)"
                    st.caption(f"{tier_badge} | G-Eval Score: **{data['geval_score']}** | Latency: **{data['latency_sec']}s**")
                    
                    # Display response
                    st.markdown(data["final_response"])
                    
                    with st.expander("🔍 View Retrieved Context (Debug)"):
                        st.markdown(data.get("context_used", "No context retrieved."))
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": data["final_response"]
                    })
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Connection failed. Is the FastAPI server running on port 8000? {str(e)}")

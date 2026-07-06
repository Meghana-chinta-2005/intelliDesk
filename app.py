"""
IntelliDesk - Streamlit Frontend
Single-page UI that calls the FastAPI /ask endpoint and displays the result.
"""

import streamlit as st
import requests

API_URL = "http://localhost:8000"

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliDesk | AI Support Assistant",
    page_icon="🧠",
    layout="centered",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .main-title { font-size: 2.2rem; font-weight: 700; color: #4F8BF9; }
        .subtitle   { color: #888; margin-top: -10px; }
        .answer-box {
            background: #1E2130;
            border-left: 4px solid #4F8BF9;
            padding: 1rem 1.2rem;
            border-radius: 6px;
            white-space: pre-wrap;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🧠 IntelliDesk</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">AI-powered internal support assistant — grounded answers from your knowledge base</p>',
    unsafe_allow_html=True,
)
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
question = st.text_area(
    "Your question",
    placeholder="e.g. How do I reset my VPN password?",
    height=100,
)

if st.button("🔍 Get Answer", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a question before submitting.")
    else:
        with st.spinner("Searching knowledge base and generating answer…"):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                st.success("Answer retrieved!")
                st.markdown(
                    f'<div class="answer-box">{data["answer"]}</div>',
                    unsafe_allow_html=True,
                )
            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Could not connect to the IntelliDesk API. "
                    "Make sure the FastAPI server is running on port 8000."
                )
            except requests.exceptions.HTTPError as exc:
                st.error(f"API error: {exc.response.status_code} — {exc.response.text}")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

st.divider()
st.caption("IntelliDesk v1.0 · Powered by FAISS + Groq · Answers grounded in company knowledge base only")

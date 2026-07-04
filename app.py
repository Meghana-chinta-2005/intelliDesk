"""Streamlit frontend entrypoint for IntelliDesk."""

import streamlit as st


st.set_page_config(page_title="IntelliDesk", page_icon="ID", layout="centered")
st.title("IntelliDesk")
st.caption("RAG-based internal support assistant")

question = st.text_input("Support question")

if st.button("Get Answer", type="primary"):
    if not question.strip():
        st.warning("Enter a support question first.")
    else:
        st.info("The API integration will be implemented in Phase 9.")

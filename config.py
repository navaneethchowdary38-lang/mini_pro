import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

def load_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=st.secrets["GOOGLE_API_KEY"]
    )

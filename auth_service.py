import requests
import streamlit as st
from firebase_admin import auth

def login(email, password):
    api_key = st.secrets["FIREBASE_WEB_API_KEY"]

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

    data = requests.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True
    }).json()

    if "error" in data:
        return None

    return auth.get_user_by_email(email)


def signup(email, password):
    try:
        return auth.create_user(email=email, password=password)
    except:
        return None

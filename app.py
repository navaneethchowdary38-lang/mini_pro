import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import os
from datetime import datetime

# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= SESSION DEFAULTS =================
defaults = {
    "user_id": "demo_user",   # replace with your auth user id
    "chats": {},
    "current_chat_id": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ================= FIREBASE FUNCTIONS =================
def load_user_chats():
    user_ref = db.collection("users").document(st.session_state.user_id)
    chats_ref = user_ref.collection("chats").stream()

    chats = {}
    for chat in chats_ref:
        chats[chat.id] = chat.to_dict()

    st.session_state.chats = chats


def save_chat(chat_id):
    user_ref = db.collection("users").document(st.session_state.user_id)
    user_ref.collection("chats").document(chat_id).set(
        st.session_state.chats[chat_id]
    )


def create_new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "created_at": datetime.utcnow(),
        "messages": []
    }
    st.session_state.current_chat_id = chat_id
    save_chat(chat_id)


# ================= LOAD CHATS ON START =================
if not st.session_state.chats:
    load_user_chats()

if not st.session_state.current_chat_id:
    if st.session_state.chats:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
    else:
        create_new_chat()

# ================= SIDEBAR =================
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    create_new_chat()
    st.rerun()

for chat_id, chat_data in st.session_state.chats.items():
    if st.sidebar.button(chat_data["title"], key=chat_id):
        st.session_state.current_chat_id = chat_id
        st.rerun()

# ================= CHAT INPUT =================
st.title("📘 SlideSense")

chat_id = st.session_state.current_chat_id
messages = st.session_state.chats[chat_id]["messages"]

question = st.chat_input("Ask something...")

if question:
    # FAKE AI RESPONSE (replace with your LLM code)
    answer = f"AI response to: {question}"

    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": answer})

    # Auto title generation
    if st.session_state.chats[chat_id]["title"] == "New Chat":
        st.session_state.chats[chat_id]["title"] = question[:40]

    save_chat(chat_id)
    st.rerun()

# ================= DISPLAY CHAT =================
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

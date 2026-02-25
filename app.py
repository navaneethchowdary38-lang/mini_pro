import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= PAGE CONFIG =================
st.set_page_config(page_title="SlideSense", page_icon="📘", layout="wide")

# ================= SESSION DEFAULTS =================
defaults = {
    "user_id": "demo_user",  # Replace with real auth user id
    "chats": {},
    "current_chat_id": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ================= LLM =================
@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash")


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


def delete_chat(chat_id):
    user_ref = db.collection("users").document(st.session_state.user_id)
    user_ref.collection("chats").document(chat_id).delete()

    st.session_state.chats.pop(chat_id)

    if st.session_state.chats:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
    else:
        create_new_chat()


def create_new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "created_at": datetime.utcnow(),
        "messages": [],
        "pdf_id": None,
        "vector_db": None
    }
    st.session_state.current_chat_id = chat_id
    save_chat(chat_id)


# ================= INITIAL LOAD =================
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
    col1, col2 = st.sidebar.columns([4, 1])

    if col1.button(chat_data["title"], key=f"select_{chat_id}"):
        st.session_state.current_chat_id = chat_id
        st.rerun()

    if col2.button("🗑", key=f"delete_{chat_id}"):
        delete_chat(chat_id)
        st.rerun()


# ================= MAIN =================
st.title("📘 SlideSense AI")

chat_id = st.session_state.current_chat_id
chat_data = st.session_state.chats[chat_id]

# ================= PDF UPLOAD =================
pdf = st.file_uploader("Upload PDF", type="pdf")

if pdf:
    pdf_id = f"{pdf.name}_{pdf.size}"

    if chat_data["pdf_id"] != pdf_id:
        with st.spinner("Processing PDF..."):
            reader = PdfReader(pdf)
            text = ""

            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=80
            )

            chunks = splitter.split_text(text)

            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            chat_data["vector_db"] = FAISS.from_texts(chunks, embeddings)
            chat_data["pdf_id"] = pdf_id

            save_chat(chat_id)


# ================= CHAT INPUT =================
question = st.chat_input("Ask about this PDF...")

if question:
    chat_data["messages"].append({
        "role": "user",
        "content": question
    })

    # 🔥 AUTO TITLE (ONLY FIRST MESSAGE)
    if len(chat_data["messages"]) == 1:
        chat_data["title"] = question[:35] + (
            "..." if len(question) > 35 else ""
        )

    if chat_data["vector_db"] is None:
        answer = "Please upload a PDF first."
    else:
        llm = load_llm()

        docs = chat_data["vector_db"].similarity_search(question, k=5)

        prompt = ChatPromptTemplate.from_template("""
Context:
{context}

Question:
{question}

Answer only from document.
""")

        chain = create_stuff_documents_chain(llm, prompt)
        result = chain.invoke({"context": docs, "question": question})

        answer = result if isinstance(result, str) else result.get("output_text", "")

    chat_data["messages"].append({
        "role": "assistant",
        "content": answer
    })

    save_chat(chat_id)
    st.rerun()


# ================= DISPLAY CHAT =================
for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime
from PyPDF2 import PdfReader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate


# ================= FIREBASE INIT =================
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="SlideSense", page_icon="📘", layout="wide")

# ================= SESSION STATE =================
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

USER_ID = "demo_user"   # Replace with your auth system


# ================= LLM =================
@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash")


# ================= FIREBASE =================
def load_chats():
    chats = {}
    docs = db.collection("users").document(USER_ID).collection("chats").stream()
    for doc in docs:
        chats[doc.id] = doc.to_dict()
    return chats


def save_chat(chat_id):
    db.collection("users").document(USER_ID).collection("chats").document(chat_id).set(
        st.session_state.chats[chat_id]
    )


def delete_chat(chat_id):
    db.collection("users").document(USER_ID).collection("chats").document(chat_id).delete()
    st.session_state.chats.pop(chat_id)


def create_new_chat():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "pdf_id": None
    }
    st.session_state.current_chat_id = chat_id
    save_chat(chat_id)


# ================= LOAD INITIAL =================
if not st.session_state.chats:
    st.session_state.chats = load_chats()

if not st.session_state.current_chat_id:
    if st.session_state.chats:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
    else:
        create_new_chat()


# ================= SIDEBAR =================
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    create_new_chat()
    st.session_state.vector_store = None
    st.rerun()

for chat_id, chat in st.session_state.chats.items():
    col1, col2 = st.sidebar.columns([4,1])

    if col1.button(chat["title"], key=f"sel_{chat_id}"):
        st.session_state.current_chat_id = chat_id
        st.session_state.vector_store = None   # reset vector store
        st.rerun()

    if col2.button("🗑", key=f"del_{chat_id}"):
        delete_chat(chat_id)
        st.session_state.vector_store = None
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
                if page.extract_text():
                    text += page.extract_text()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=80
            )

            chunks = splitter.split_text(text)

            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            st.session_state.vector_store = FAISS.from_texts(chunks, embeddings)
            chat_data["pdf_id"] = pdf_id

            save_chat(chat_id)


# ================= CHAT =================
question = st.chat_input("Ask about this PDF")

if question:

    chat_data["messages"].append({"role": "user", "content": question})

    # ✅ TITLE FIX
    if len(chat_data["messages"]) == 1:
        chat_data["title"] = question[:30] + ("..." if len(question) > 30 else "")

    if st.session_state.vector_store is None:
        answer = "Please upload a PDF first."
    else:
        llm = load_llm()
        docs = st.session_state.vector_store.similarity_search(question, k=5)

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

    chat_data["messages"].append({"role": "assistant", "content": answer})

    save_chat(chat_id)
    st.rerun()


# ================= DISPLAY =================
for msg in chat_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

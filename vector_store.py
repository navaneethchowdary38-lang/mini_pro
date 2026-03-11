import os
import hashlib
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

VECTOR_PATH = "vector_store"


def get_pdf_hash(pdf_file):
    pdf_bytes = pdf_file.getvalue()
    return hashlib.md5(pdf_bytes).hexdigest()


def load_or_create_vector_db(chunks, pdf_file):

    os.makedirs(VECTOR_PATH, exist_ok=True)

    pdf_hash = get_pdf_hash(pdf_file)

    index_path = os.path.join(VECTOR_PATH, pdf_hash)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Load existing vector DB
    if os.path.exists(index_path):
        return FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

    # Create new vector DB
    vector_db = FAISS.from_texts(chunks, embeddings)

    vector_db.save_local(index_path)

    return vector_db

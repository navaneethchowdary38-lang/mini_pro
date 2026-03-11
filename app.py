import streamlit as st

from config import load_llm
from pdf_processor import extract_text, split_text
from vector_store import load_or_create_vector_db
from qa_chain import ask_question
from image_qa import ask_image_question

st.set_page_config(page_title="SlideSense AI")

st.title("🧠 SlideSense")

mode = st.radio("Mode", ["PDF", "Image"])

llm = load_llm()

if mode == "PDF":

    pdf = st.file_uploader("Upload PDF")

    if pdf:

        text = extract_text(pdf)

        chunks = split_text(text)

        vector_db = build_vector_db(chunks)

        question = st.text_input("Ask question")

        if question:

            answer = ask_question(llm, vector_db, question)

            st.write(answer)

else:

    image = st.file_uploader("Upload Image")

    question = st.text_input("Ask about the image")

    if image and question:

        answer = ask_image_question(llm, image, question)

        st.write(answer)

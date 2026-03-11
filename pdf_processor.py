from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text(file):

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content

    return text


def split_text(text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    return splitter.split_text(text)

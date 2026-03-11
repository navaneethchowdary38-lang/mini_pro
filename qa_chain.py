from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate


PROMPT = """
Answer the question using ONLY the provided context.

Context:
{context}

Question:
{input}

If the answer is not present say:
"Information not found in document."
"""


def ask_question(llm, vector_db, question):

    docs = vector_db.similarity_search(question, k=6)

    chain = create_stuff_documents_chain(
        llm,
        ChatPromptTemplate.from_template(PROMPT)
    )

    result = chain.invoke({
        "context": docs,
        "input": question
    })

    if isinstance(result, str):
        return result

    return result.get("output_text", "")

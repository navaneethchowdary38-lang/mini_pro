import base64
from langchain_core.messages import HumanMessage


def ask_image_question(llm, image_file, question):

    image_bytes = image_file.getvalue()

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    response = llm.invoke([HumanMessage(content=[
        {"type": "text", "text": question},
        {"type": "image_url",
         "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
    ])])

    return response.content

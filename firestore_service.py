from firebase_admin import firestore
from datetime import datetime
import uuid

db = firestore.client()


def create_chat(user_id, mode):
    chat_id = str(uuid.uuid4())

    db.collection("users").document(user_id)\
      .collection("chats").document(chat_id).set({
        "mode": mode,
        "created_at": datetime.utcnow()
      })

    return chat_id


def save_message(user_id, chat_id, role, content):
    db.collection("users").document(user_id)\
      .collection("chats").document(chat_id)\
      .collection("messages").add({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
      })


def load_messages(user_id, chat_id):

    docs = db.collection("users").document(user_id)\
        .collection("chats").document(chat_id)\
        .collection("messages").order_by("timestamp").stream()

    return [(d.to_dict()["role"], d.to_dict()["content"]) for d in docs]

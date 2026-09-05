import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# On Render: paste the full firebase-credentials.json content into an env
# var named FIREBASE_CREDENTIALS_JSON. Locally: keeps using the file, so
# nothing changes on your machine.
firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

if firebase_creds_json:
    cred = credentials.Certificate(json.loads(firebase_creds_json))
else:
    cred = credentials.Certificate("firebase-credentials.json")

firebase_admin.initialize_app(cred)

db = firestore.client()


def get_farmer_state(phone_number):
    doc_ref = db.collection("farmers").document(phone_number)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


def set_farmer_state(phone_number, data):
    doc_ref = db.collection("farmers").document(phone_number)
    doc_ref.set(data, merge=True)


def is_message_processed(message_id):
    doc_ref = db.collection("processed_messages").document(message_id)
    return doc_ref.get().exists


def mark_message_processed(message_id):
    doc_ref = db.collection("processed_messages").document(message_id)
    doc_ref.set({"processed": True})
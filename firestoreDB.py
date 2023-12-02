import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os


keyFileName = '/home/kiritian/PYTHON/purrfectplateKey.json'
fullPath = keyFileName

# Use a service account.
cred = credentials.Certificate(fullPath)

app = firebase_admin.initialize_app(cred)

db = firestore.client()


def AddNewDocument(collectionName, data):
    doc_ref = db.collection(collectionName).document()
    doc_ref.set(data)

def AddNewDocument(collectionName, documentName, data):
    doc_ref = db.collection(collectionName).document(documentName)
    doc_ref.set(data)

def get_document_by_id(collection_name, document_id):
    doc_ref = db.collection(collection_name).document(document_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc
    else:
        print(f"Document {document_id} does not exist in {collection_name} collection.")
        return None


def get_field(collection_name, document_id, field_name):
    document = get_document_by_id(collection_name, document_id)
    return document.get(field_name)

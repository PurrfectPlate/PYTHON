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


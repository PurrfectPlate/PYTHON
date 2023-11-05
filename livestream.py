import firestoreDB
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

class YouTubeLivestreamManager:
    def __init__(self, firestore_collection, firestore_document):
        self.firestore_collection = firestore_collection
        self.firestore_document = firestore_document
        self.youtube = self._setup_youtube_api()
        
    def __init__(self, firestore_document):
        self.firestore_collection = "Livestream"
        self.firestore_document = firestore_document
        self.livestream_id = ""
        self.youtube = self._setup_youtube_api()
    
    def _setup_youtube_api(self):
        db = firestoreDB.db

        doc_ref = db.collection(self.firestore_collection).document(self.firestore_document)
        doc = doc_ref.get()

        if doc.exists:
            firestore_credentials = doc.to_dict()["jsonKeyFile"]
            firestore_credentials["private_key"] = firestore_credentials["private_key"].replace('\\n', '\n')
            print(f"FIRESTORE CREDENTIALS: {firestore_credentials}")
        else:
            raise Exception("Firestore document not found")

        credentials_file = "temp_credentials.json"
        with open(credentials_file, "w") as json_file:
            json.dump(firestore_credentials, json_file)

        scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
        credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)

        return build('youtube', 'v3', credentials=credentials)

    def start_livestream(self, title, description):
        request = self.youtube.liveStreams().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': title,
                    'description': description,
                },
                'status': {
                    'privacyStatus': 'unlisted',
                }
            }
        )
        response = request.execute()
        self.livestream_id = response['id']
        return response['id']

    def stop_livestream(self):
        request = self.youtube.liveBroadcasts().transition(
            broadcastStatus='complete',
            id=self.livestream_id
        )
        request.execute()
        
    def get_stream_key(self):
        # Set up the necessary information
        API_SERVICE_NAME = 'youtube'
        API_VERSION = 'v3'
        YOUR_API_KEY = 'AIzaSyDFejJ28ov_3MQ_7gh__WSilzL9t6sD2vg'  # Replace with your actual API key

        # Create a YouTube Data API service object
        youtube = build(API_SERVICE_NAME, API_VERSION, developerKey=YOUR_API_KEY)

        # Request to retrieve the stream key
        live_broadcasts_response = youtube.liveBroadcasts().list(
            part="id,snippet",
            broadcastType="persistent"
        ).execute()

        # Extract the stream key from the response
        for broadcast in live_broadcasts_response.get("items", []):
            # Assuming you want the stream key for the first broadcast
            stream_key = broadcast['snippet']['contentDetails']['boundStreamId']
            print(f"Stream key: {stream_key}")
    
    def clean_up(self):
        # Clean up: Remove the temporary credentials file
        os.remove("temp_credentials.json")



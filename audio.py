import base64 
import firestoreDB
import os
from playsound import playsound

class AudioPlayer:

    def get_audio(self):
        return firestoreDB.get_field(self.collection_name, self.collection_id, "RecordingFile")

    def save_base64_as_mp3(self, base64_audio):
        # Decode base64 audio
        base64_audio = base64_audio.removeprefix("data:audio/mp3;base64,")
        audio_bytes = base64.urlsafe_b64decode(base64_audio)
    
        # Specify the file path where the audio will be saved
        folder_path = '.tempaudio'
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "tempsound" + '.mp3')
    
    # Convert base64 audio to MP3 format
        with open(file_path, 'wb') as file:
            file.write(audio_bytes)
    
        print(f"Audio saved as {file_path}")
        return file_path

    def delete_audio_file(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            print(f"{self.file_path} deleted successfully")
        else:
            print(f"File {self.file_path} does not exist")
    
    def __init__(self, collection_id):
        self.collection_name = "Speak_To_Device"
        self.collection_id = collection_id
        self.file_path = self.save_base64_as_mp3(self.get_audio())
        playsound(self.file_path)
        self.delete_audio_file()
    
audioplayer = AudioPlayer("xsCF6XVvWMAp613ZhS3f")

import base64 
import firestoreDB
import os
from playsound import playsound

class AudioPlayer:
    

    def get_audio(self, collection_name = "Speak_To_Device"):
        return firestoreDB.get_field(collection_name, self.collection_id, "RecordingFile")

    def save_base64_as_mp3(self, base64_audio, slot = 0):
        # Decode base64 audio
        base64_audio = base64_audio.removeprefix("data:audio/mp3;base64,")
        base64_audio = base64_audio.removeprefix("data:audio/mpeg;base64,")
        audio_bytes = base64.urlsafe_b64decode(base64_audio)
    
        folder_path = '.tempaudio'
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, "tempsound" + f"{slot}" + '.mp3')
    
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
    
    def play_sound(self):
        if self.isPlaying:
            return
        self.isPlaying = True
        playsound(self.file_path)
        if(self.collection_name == "Speak_To_Device"):
            doc_ref = firestoreDB.db.collection(self.collection_name).document(self.collection_id)
            doc_ref.delete()
        self.isPlaying = False
    
    
    def __init__(self, collection_id, collection_name = "Speak_To_Device", slot = 0):
        self.collection_id = collection_id
        self.slot = slot
        self.collection_name = collection_name
        self.file_path = self.save_base64_as_mp3(self.get_audio(collection_name), self.slot)
        self.isPlaying = False
        #self.play_sound()
        #self.delete_audio_file()

    

if __name__ == "__main__":
    audio = AudioPlayer("JyQJL5ilOV9NtzLk9Kfx")
    if audio.play_sound():
        print("SOUND DONEE")
    
    


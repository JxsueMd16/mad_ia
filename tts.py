import os
from dotenv import load_dotenv
import requests
from gtts import gTTS

# Texto a voz con ElevenLabs y fallback offline (gTTS)
class TTS:
    def __init__(self):
        load_dotenv()
        self.key = os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = "pNInz6obpgDQGcFmaJgB"  # voz base; puedes cambiarla en tu cuenta

    def process(self, text):
        CHUNK_SIZE = 1024
        file_name = "response.mp3"
        os.makedirs("static", exist_ok=True)
        file_path = os.path.join("static", file_name)

        # Intento ElevenLabs
        try:
            if not self.key:
                raise Exception("ELEVENLABS_API_KEY no configurada")

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.key
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v1",
                "voice_settings": {"stability": 0.55, "similarity_boost": 0.55}
            }
            response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
            print("TTS status:", response.status_code)

            if response.status_code != 200:
                print("TTS ERROR:", response.text)
                raise Exception("Fallo ElevenLabs")

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
            return file_name

        except Exception as e:
            print("Usando gTTS como fallback debido a:", e)
            # Fallback gTTS
            try:
                tts = gTTS(text=text, lang='es')
                tts.save(file_path)
                return file_name
            except Exception as e2:
                print("Fallo también gTTS:", e2)
                return None

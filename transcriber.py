import os
from openai import OpenAI
import tempfile

class Transcriber:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def transcribe(self, audio_file_storage):
        """
        Transcribe audio usando Whisper con configuración optimizada
        """
        # Guardar temporalmente el archivo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            audio_file_storage.save(tmp.name)
            tmp.flush()
            
            try:
                # Abrir y transcribir con parámetros optimizados
                with open(tmp.name, "rb") as af:
                    result = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=af,
                        language="es",  # Fuerza español para mejor precisión
                        prompt="Transcripción en español de una conversación clara.",  # Guía el modelo
                        temperature=0.0  # Más determinístico, menos alucinaciones
                    )
                    
                    text = result.text.strip()
                    
                    # Filtrar transcripciones sospechosas
                    if self._is_garbage(text):
                        return ""
                    
                    return text
                    
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(tmp.name)
                except:
                    pass
    
    def _is_garbage(self, text):
        """
        Detecta transcripciones basura (ruido, música, silencios)
        """
        if not text or len(text.strip()) < 2:
            return True
        
        # Lista de frases típicas de ruido/música (más específico)
        garbage_phrases = [
            "thanks for watching",
            "thank you for watching", 
            "don't forget to subscribe",
            "like and subscribe",
            "[music]",
            "[applause]",
            "(music)",
            "(applause)",
        ]
        
        text_lower = text.lower()
        for phrase in garbage_phrases:
            if phrase in text_lower:
                return True
        
        # Detectar si TODO el texto son emojis/símbolos musicales
        if all(c in "♪🎵🎶😊👍" or c.isspace() for c in text):
            return True
        
        # Detectar si es mayormente caracteres no latinos (>70%)
        non_latin = sum(1 for c in text if ord(c) > 0x024F and not c.isspace())
        if len(text) > 5 and non_latin / len(text) > 0.7:
            return True
        
        # Detectar repeticiones simples como "a a a a a"
        words = text.split()
        if len(words) >= 4 and len(set(words)) == 1:
            return True
        
        return False
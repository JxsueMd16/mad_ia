import openai
import tempfile
import os

class Transcriber:
    def __init__(self):
        pass

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
                    result = openai.Audio.transcribe(
                        "whisper-1",
                        af,
                        language="es",  # Fuerza español para mejor precisión
                        prompt="Transcripción en español de una conversación clara.",  # Guía el modelo
                        temperature=0.0  # Más determinístico, menos alucinaciones
                    )
                    
                    text = result.get("text", "").strip()
                    
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
        
        # Lista de frases típicas de ruido/música
        garbage_phrases = [
            "thanks for watching",
            "thank you for watching",
            "subscribe",
            "like and subscribe",
            "music",
            "♪",
            "🎵",
            "😊",
            "[music]",
            "[applause]",
            "subtitles by",
        ]
        
        text_lower = text.lower()
        for phrase in garbage_phrases:
            if phrase in text_lower:
                return True
        
        # Detectar si es mayormente caracteres no latinos (coreano, chino, etc.)
        non_latin = sum(1 for c in text if ord(c) > 0x024F)
        if len(text) > 0 and non_latin / len(text) > 0.3:
            return True
        
        # Detectar repeticiones simples como "You You" o "a a a"
        words = text.split()
        if len(words) >= 2 and len(set(words)) == 1:
            return True
        
        return False
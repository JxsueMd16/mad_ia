import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, render_template, request, session

from transcriber import Transcriber
from llm import LLM
from tts import TTS

# Cargar llaves del archivo .env
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configurar Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "Jxxmd16_app"

@app.route("/")
def index():
    return render_template("recorder.html")

@app.route("/audio", methods=["POST"])
def audio():
    try:
        audio = request.files.get("audio")
        if not audio:
            return {"result": "error", "text": "No llegó el archivo de audio."}, 400

        # 1) Transcribir con validación
        text = Transcriber().transcribe(audio)
        print(f"Texto transcrito: '{text}'")

        # Validar que hay texto útil
        if not text or len(text.strip()) < 2:
            return {
                "result": "error",
                "text": "No se detectó audio claro. Intenta hablar más cerca del micrófono."
            }, 200

        # 2) LLM (chat corto, estilo electrónica)
        history = session.get("chat_history", None)
        llm = LLM(history)
        final_response = llm.chat(text)

        # Validar respuesta
        if not final_response or len(final_response.strip()) < 2:
            final_response = "No procesé eso. Repite por favor."

        # 3) Guardar contexto (últimos 10 mensajes)
        session["chat_history"] = llm.messages[-10:]

        # 4) TTS
        tts_file = TTS().process(final_response)

        return {
            "result": "ok",
            "text": final_response,
            "file": tts_file
        }, 200

    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
        return {
            "result": "error",
            "text": "Error del servidor. Revisa la consola."
        }, 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
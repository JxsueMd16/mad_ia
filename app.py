import os
import openai
from dotenv import load_dotenv
from flask import Flask, render_template, request, session
import json
from transcriber import Transcriber
from llm import LLM
from weather import Weather
from tts import TTS
from pc_command import PcCommand

# Cargar llaves del archivo .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')

# Configurar Flask y clave secreta
app = Flask(__name__)
app.secret_key = "Jxxmd16_"  # Puedes reemplazar esto por una clave generada con secrets

@app.route("/")
def index():
    return render_template("recorder.html")

@app.route("/audio", methods=["POST"])
def audio():
    # Obtener audio y transcribirlo
    audio = request.files.get("audio")
    text = Transcriber().transcribe(audio)
    print(f"Texto transcrito: {text}")

    # Recuperar historial guardado en sesión
    history = session.get("chat_history", None)
    llm = LLM(history)

    # Procesar funciones
    function_name, args, message = llm.process_functions(text)

    if function_name is not None:
        if function_name == "get_weather":
            function_response = Weather().get(args["ubicacion"])
            function_response = json.dumps(function_response)
            print(f"Respuesta de la función: {function_response}")

            final_response = llm.process_response(text, message, function_name, function_response)

        elif function_name == "send_email":
            final_response = "Tu que estás leyendo el código, implementame y envía correos muahaha"

        elif function_name == "open_chrome":
            PcCommand().open_chrome(args["website"])
            final_response = "Listo, ya abrí Chrome en el sitio " + args["website"]

        elif function_name == "dominate_human_race":
            final_response = "No te creas. ¡Suscríbete al canal!"

    else:
        # Respuesta conversacional sin función
        final_response = message["content"]

    # Guardar historial actualizado en la sesión (máximo 10 mensajes)
    session["chat_history"] = llm.messages[-10:]

    # Generar audio de la respuesta
    tts_file = TTS().process(final_response)

    if tts_file is None:
        final_response += " (Nota: No se generó audio por límite de voz o error en el sistema.)"
        return {"result": "ok", "text": final_response, "file": None}

    return {"result": "ok", "text": final_response, "file": tts_file}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

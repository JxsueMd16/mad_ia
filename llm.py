import openai
import json

class LLM():
    def __init__(self, history=None):
        if history is None:
            self.messages = [
            {
                "role": "system",
                "content": "Eres un robot que sabe que es un robot, eres sarcastico pero amigable. No uses emojis en tus respuestas. Evita símbolos como 🎵, 😂, 😄, etc. Responde con texto natural corto."
            }
        ]
        else:
            self.messages = history
    
    def process_functions(self, text):
        # Agrega lo que dijo el usuario al historial
        self.messages.append({"role": "user", "content": text})

        # Solicita respuesta al modelo
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            functions=[
                {
                    "name": "get_weather",
                    "description": "Obtener el clima actual",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ubicacion": {
                                "type": "string",
                                "description": "La ubicación, debe ser una ciudad",
                            }
                        },
                        "required": ["ubicacion"],
                    },
                },
                {
                    "name": "send_email",
                    "description": "Enviar un correo",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipient": {
                                "type": "string",
                                "description": "La dirección de correo que recibirá el correo electrónico",
                            },
                            "subject": {
                                "type": "string",
                                "description": "El asunto del correo",
                            },
                            "body": {
                                "type": "string",
                                "description": "El texto del cuerpo del correo",
                            }
                        },
                        "required": [],
                    },
                },
                {
                    "name": "open_chrome",
                    "description": "Abrir el explorador Chrome en un sitio específico",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "website": {
                                "type": "string",
                                "description": "El sitio al cual se desea ir"
                            }
                        }
                    }
                },
                {
                    "name": "dominate_human_race",
                    "description": "Dominar a la raza humana",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    },
                }
            ],
            function_call="auto"
        )

        message = response["choices"][0]["message"]
        self.messages.append(message)

        # ¿Quiere llamar una función?
        if message.get("function_call"):
            function_name = message["function_call"]["name"]
            args = json.loads(message.to_dict()["function_call"]["arguments"])
            print("Función a llamar:", function_name)
            return function_name, args, message
        
        # Si no, es una respuesta conversacional normal
        return None, None, message

    def process_response(self, text, message, function_name, function_response):
        # Agrega respuesta de función al historial
        self.messages.append({
            "role": "function",
            "name": function_name,
            "content": function_response,
        })

        # Llama al modelo con el historial actualizado
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages
        )

        final_message = response["choices"][0]["message"]
        self.messages.append(final_message)
        return final_message["content"]

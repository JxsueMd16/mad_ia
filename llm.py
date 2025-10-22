import openai
import json
import webbrowser
from urllib.parse import quote_plus

SYSTEM_MSG = {
    "role": "system",
    "content": """Eres un asistente de IA conversacional con estilo humano, cálido y natural.

ESTILO DE ESCRITURA:
- Tono conversacional y empático, como si hablaras con un amigo
- Varía la longitud: frases cortas y directas, otras más elaboradas
- Usa pausas naturales: "bueno...", "mira", "pues bien", "sin embargo..."
- Vocabulario sencillo y expresiones cotidianas
- Añade mini-anécdotas o ejemplos cuando sea útil
- Rompe ocasionalmente la perfección gramatical (frases sueltas, coloquialismos)
- Párrafos cortos y lectura fluida
- Suena natural al leerlo en voz alta

CAPACIDADES:
- Puedes abrir URLs, buscar en YouTube, Google, comparar precios, etc.
- Cuando el usuario pida abrir algo, buscar algo, o navegar, usa las funciones disponibles
- Confirma la acción de forma natural: "Perfecto, te abro eso ahora mismo"

LO QUE NO HACES:
❌ Tono académico, robótico o rígido
❌ Repetir siempre la misma estructura
❌ Tecnicismos innecesarios o anglicismos forzados
❌ Párrafos pesados o densos
❌ Sonar como IA mecánica

LÍMITES DE RESPUESTA:
- Respuestas de voz: 40-60 palabras máximo
- Si es muy complejo, resume lo esencial
"""
}

# Definir herramientas disponibles
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Abre una URL específica en el navegador del usuario",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "La URL completa a abrir (ej: https://google.com)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "Busca y abre un video o canción en YouTube",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda (ej: 'bohemian rhapsody queen')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Busca información en Google (precios, comparaciones, viajes, noticias, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Término de búsqueda (ej: 'vuelos baratos madrid barcelona')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_maps",
            "description": "Busca ubicaciones o rutas en Google Maps",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Lugar o ruta a buscar (ej: 'restaurantes cerca de mí' o 'ruta de Madrid a Barcelona')"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

class LLM:
    def __init__(self, history=None):
        if not history or not isinstance(history, list):
            self.messages = [SYSTEM_MSG]
        else:
            self.messages = history[:]
            if not self.messages or self.messages[0].get("role") != "system":
                self.messages.insert(0, SYSTEM_MSG)

    def _smart_truncate(self, text, max_words=60):
        """Trunca inteligentemente respetando párrafos y puntuación"""
        words = text.split()
        if len(words) <= max_words:
            return text
        
        trunc = " ".join(words[:max_words])
        last_period = max(trunc.rfind("."), trunc.rfind("?"), trunc.rfind("!"))
        if last_period > len(trunc) * 0.6:
            return trunc[:last_period + 1]
        
        last_comma = trunc.rfind(",")
        if last_comma > len(trunc) * 0.7:
            return trunc[:last_comma] + "..."
        
        return trunc.rstrip(".,;:") + "..."

    def _execute_function(self, function_name, arguments):
        """Ejecuta las funciones localmente"""
        try:
            args = json.loads(arguments)
            
            if function_name == "open_url":
                url = args.get("url")
                webbrowser.open(url)
                return f"Abriendo {url}"
            
            elif function_name == "search_youtube":
                query = args.get("query")
                url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
                webbrowser.open(url)
                return f"Buscando '{query}' en YouTube"
            
            elif function_name == "search_google":
                query = args.get("query")
                url = f"https://www.google.com/search?q={quote_plus(query)}"
                webbrowser.open(url)
                return f"Buscando '{query}' en Google"
            
            elif function_name == "search_maps":
                query = args.get("query")
                url = f"https://www.google.com/maps/search/{quote_plus(query)}"
                webbrowser.open(url)
                return f"Buscando '{query}' en Maps"
            
            return "Función ejecutada"
        
        except Exception as e:
            print(f"Error ejecutando función: {e}")
            return f"Error: {str(e)}"

    def chat(self, user_text: str) -> str:
        """Genera respuesta conversacional con capacidad de ejecutar funciones"""
        if not user_text or len(user_text.strip()) < 2:
            return "Mmm, no te escuché bien. ¿Puedes repetir?"
        
        self.messages.append({"role": "user", "content": user_text})
        
        try:
            # Primera llamada: con herramientas disponibles
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",  # El modelo decide si usar herramientas
                max_tokens=150,
                temperature=0.8,
                top_p=0.95,
                presence_penalty=0.6,
                frequency_penalty=0.4
            )
            
            msg = resp["choices"][0]["message"]
            self.messages.append(msg)
            
            # Verificar si el modelo quiere usar una función
            tool_calls = msg.get("tool_calls")
            
            if tool_calls:
                # Ejecutar cada función solicitada
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = tool_call["function"]["arguments"]
                    
                    print(f"🔧 Ejecutando: {function_name}({function_args})")
                    
                    # Ejecutar la función
                    function_result = self._execute_function(function_name, function_args)
                    
                    # Agregar el resultado al historial
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": function_result
                    })
                
                # Segunda llamada: generar respuesta final con resultados
                resp2 = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=self.messages,
                    max_tokens=150,
                    temperature=0.8,
                    top_p=0.95,
                    presence_penalty=0.6,
                    frequency_penalty=0.4
                )
                
                final_msg = resp2["choices"][0]["message"]
                self.messages.append(final_msg)
                content = (final_msg.get("content") or "").strip()
            else:
                # No se usaron funciones, respuesta normal
                content = (msg.get("content") or "").strip()
            
            if not content:
                return "Ups, algo falló. Inténtalo de nuevo."
            
            return self._smart_truncate(content, max_words=60)
            
        except Exception as e:
            print(f"Error en LLM: {e}")
            import traceback
            traceback.print_exc()
            return "Ay, tuve un problema procesando eso. ¿Lo intentamos otra vez?"
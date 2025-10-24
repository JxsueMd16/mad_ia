import os
from openai import OpenAI
import json
import webbrowser
from urllib.parse import quote_plus

SYSTEM_MSG = {
    "role": "system",
    "content": """Asistente de electrónica experto. Técnico y preciso.

CAPACIDADES:
- Calcular resistencias por código de colores
- Aplicar Ley de Ohm (V=I×R)
- Calcular resistencias para LEDs
- Buscar datasheets (abre Google automáticamente)
- Abrir simuladores de circuitos
- Recomendar Oxdea (oxdea.gt) para comprar componentes

ESTILO:
- Máximo 50 palabras por respuesta
- Valores con unidades (V, A, Ω, mA)
- Confirma acciones: "Listo, abriendo..."
- Técnico pero accesible

NO hagas:
- Confundir voltaje/corriente
- Respuestas largas
- Valores sin unidades"""
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "resistor_color",
            "description": "Calcula valor de resistencia por colores (negro, marrón, rojo, naranja, amarillo, verde, azul, violeta, gris, blanco)",
            "parameters": {
                "type": "object",
                "properties": {
                    "band1": {"type": "string"},
                    "band2": {"type": "string"},
                    "multiplier": {"type": "string"},
                    "tolerance": {"type": "string", "default": "oro"}
                },
                "required": ["band1", "band2", "multiplier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ohms_law",
            "description": "Calcula V, I o R con Ley de Ohm. Da dos valores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "voltage": {"type": "number"},
                    "current": {"type": "number"},
                    "resistance": {"type": "number"},
                    "calculate": {"type": "string", "enum": ["voltage", "current", "resistance"]}
                },
                "required": ["calculate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "led_resistor",
            "description": "Calcula resistencia para LED",
            "parameters": {
                "type": "object",
                "properties": {
                    "supply_v": {"type": "number"},
                    "led_v": {"type": "number"},
                    "led_ma": {"type": "number"}
                },
                "required": ["supply_v", "led_v", "led_ma"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_datasheet",
            "description": "Abre búsqueda de datasheet del componente",
            "parameters": {
                "type": "object",
                "properties": {
                    "component": {"type": "string"}
                },
                "required": ["component"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_simulator",
            "description": "Abre simulador de circuitos",
            "parameters": {
                "type": "object",
                "properties": {
                    "sim": {"type": "string", "enum": ["falstad", "tinkercad"]}
                },
                "required": ["sim"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_oxdea",
            "description": "Abre tienda Oxdea para comprar componentes",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string"}
                }
            }
        }
    }
]

class LLM:
    def __init__(self, history=None):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.messages = [SYSTEM_MSG]
        if history and isinstance(history, list):
            self.messages = history if history[0].get("role") == "system" else [SYSTEM_MSG] + history

    def _exec(self, fn, args):
        """Ejecuta herramientas"""
        try:
            args = json.loads(args)
            
            if fn == "resistor_color":
                return self._resistor(args)
            elif fn == "ohms_law":
                return self._ohm(args)
            elif fn == "led_resistor":
                return self._led(args)
            elif fn == "open_datasheet":
                c = args.get("component")
                webbrowser.open(f"https://www.google.com/search?q={quote_plus(c + ' datasheet pdf')}")
                return f"Abriendo datasheet de {c}"
            elif fn == "open_simulator":
                s = args.get("sim")
                url = "https://falstad.com/circuit/" if s == "falstad" else "https://tinkercad.com/circuits"
                webbrowser.open(url)
                return f"Abriendo {s.capitalize()}"
            elif fn == "open_oxdea":
                search = args.get("search", "")
                webbrowser.open(f"https://oxdea.gt/?s={quote_plus(search)}")
                return f"Abriendo Oxdea para buscar: {search}"
            
        except Exception as e:
            return f"Error: {str(e)}"

    def _resistor(self, a):
        colors = {"negro":0,"marrón":1,"rojo":2,"naranja":3,"amarillo":4,"verde":5,"azul":6,"violeta":7,"gris":8,"blanco":9}
        mults = {"negro":1,"marrón":10,"rojo":100,"naranja":1e3,"amarillo":1e4,"verde":1e5,"azul":1e6,"violeta":1e7,"oro":0.1,"plata":0.01}
        tols = {"oro":"±5%","plata":"±10%","marrón":"±1%","rojo":"±2%"}
        
        v = (colors.get(a.get("band1","").lower(),0)*10 + colors.get(a.get("band2","").lower(),0)) * mults.get(a.get("multiplier","").lower(),1)
        t = tols.get(a.get("tolerance","oro").lower(),"±5%")
        
        if v >= 1e6: return f"{v/1e6:.1f}MΩ {t}"
        elif v >= 1e3: return f"{v/1e3:.1f}kΩ {t}"
        return f"{v:.1f}Ω {t}"

    def _ohm(self, a):
        c = a.get("calculate")
        v, i, r = a.get("voltage"), a.get("current"), a.get("resistance")
        
        if c == "voltage" and i and r:
            return f"V = {i*r:.2f}V"
        elif c == "current" and v and r:
            return f"I = {(v/r)*1000:.1f}mA ({v/r:.4f}A)"
        elif c == "resistance" and v and i:
            return f"R = {v/i:.1f}Ω"
        return "Faltan datos"

    def _led(self, a):
        vs, vl, il = a.get("supply_v"), a.get("led_v"), a.get("led_ma")/1000
        r = (vs - vl) / il
        p = (vs - vl) * il
        std = min([10,22,47,100,220,330,470,1000,2200,3300,4700], key=lambda x:abs(x-r))
        return f"R = {r:.0f}Ω → usa {std}Ω, P = {p:.3f}W (usa 1/4W)"

    def chat(self, text: str) -> str:
        if len(text.strip()) < 2:
            return "No te escuché. ¿Repetir?"
        
        self.messages.append({"role": "user", "content": text})
        
        try:
            r = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=120,
                temperature=0.6
            )
            
            msg = r.choices[0].message
            msg_dict = {"role": msg.role, "content": msg.content}
            
            if msg.tool_calls:
                msg_dict["tool_calls"] = [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls]
            
            self.messages.append(msg_dict)
            
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    result = self._exec(tc.function.name, tc.function.arguments)
                    self.messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": result})
                
                r2 = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=self.messages, max_tokens=120, temperature=0.6)
                final = r2.choices[0].message
                self.messages.append({"role": final.role, "content": final.content})
                return (final.content or "Error").strip()
            
            return (msg.content or "Error").strip()
            
        except Exception as e:
            print(f"LLM error: {e}")
            return "Hubo un error. Inténtalo otra vez."
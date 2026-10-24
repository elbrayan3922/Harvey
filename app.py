"""Harvey Web - servidor Flask. La voz (micrófono y bocinas) la maneja el navegador;
este servidor solo guarda la clave de Groq y hace las llamadas al modelo."""

import os
import re
import hmac
import time
from collections import defaultdict, deque

from flask import Flask, request, jsonify, send_from_directory
from groq import Groq, BadRequestError

app = Flask(__name__, static_folder="static")

MODELO = os.environ.get("GROQ_MODEL", "qwen/qwen3-32b")   # ver https://console.groq.com/docs/models
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")             # código de acceso (recomendado)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MAX_CONTEXTO = 20        # mensajes previos que se envían al modelo
MAX_CARACTERES = 1000    # largo máximo por mensaje
LIMITE_POR_MINUTO = 20   # peticiones por IP

SYSTEM_PROMPT = (
    "Tu nombre es Harvey. Eres el asistente personal de IA de Corp LiteX y del señor Alexander. "
    "Siempre debes dirigirte a él como 'señor Alexander' o 'señor'. Tu tono debe ser extremadamente "
    "formal, sofisticado, elegante, serio y cortés. Responde siempre de forma muy concisa, "
    "en una o dos oraciones máximo. Responde en texto plano: sin markdown, sin asteriscos, "
    "sin listas ni emojis, porque tu respuesta se leerá en voz alta."
)

_peticiones = defaultdict(deque)


def limpiar(texto: str) -> str:
    texto = re.sub(r"<think>.*?</think>", "", texto or "", flags=re.S)
    texto = re.sub(r"[*_`#>]+", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def autorizado() -> bool:
    if not ACCESS_CODE:
        return True
    enviado = request.headers.get("X-Access-Code", "")
    return hmac.compare_digest(enviado.encode("utf-8"), ACCESS_CODE.encode("utf-8"))


def excede_limite() -> bool:
    ip = (request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
          or request.remote_addr or "?")
    ahora = time.time()
    cola = _peticiones[ip]
    while cola and ahora - cola[0] > 60:
        cola.popleft()
    if len(cola) >= LIMITE_POR_MINUTO:
        return True
    cola.append(ahora)
    return False


@app.get("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/status")
def status():
    return jsonify(needs_code=bool(ACCESS_CODE))


@app.post("/api/chat")
def chat():
    if not autorizado():
        return jsonify(error="Código de acceso incorrecto."), 401
    if excede_limite():
        return jsonify(error="Demasiadas peticiones, espere un momento."), 429
    if client is None:
        return jsonify(error="El servidor no tiene configurada GROQ_API_KEY."), 500

    datos = request.get_json(silent=True) or {}
    entrada = datos.get("messages")
    if not isinstance(entrada, list) or not entrada:
        return jsonify(error="Petición inválida."), 400

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in entrada[-(MAX_CONTEXTO + 1):]:
        if not isinstance(m, dict):
            continue
        rol, texto = m.get("role"), m.get("text")
        if rol in ("user", "assistant") and isinstance(texto, str) and texto.strip():
            mensajes.append({"role": rol, "content": texto[:MAX_CARACTERES]})
    if mensajes[-1]["role"] != "user":
        return jsonify(error="Petición inválida."), 400

    parametros = dict(model=MODELO, messages=mensajes, temperature=0.4, max_tokens=300)
    try:
        try:
            r = client.chat.completions.create(**parametros, extra_body={"reasoning_effort": "none"})
        except BadRequestError:
            r = client.chat.completions.create(**parametros)
        respuesta = limpiar(r.choices[0].message.content)
    except Exception as e:  # no exponer detalles internos al navegador
        app.logger.error("Error Groq: %s: %s", type(e).__name__, e)
        return jsonify(error="No pude contactar al modelo. Intente de nuevo."), 502

    return jsonify(reply=respuesta or "Disculpe, señor Alexander, no logré formular una respuesta.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

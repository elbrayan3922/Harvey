# Harvey Web

Asistente de voz en el navegador. El navegador escucha y habla; el servidor (Flask) guarda tu
clave de Groq y llama al modelo.

## Probarlo en tu computadora
    py -m pip install -r requirements.txt
    set GROQ_API_KEY=tu_clave_nueva          (PowerShell:  $env:GROQ_API_KEY="tu_clave_nueva")
    set ACCESS_CODE=un_codigo_que_tu_elijas  (PowerShell:  $env:ACCESS_CODE="...")
    py app.py
Abre http://localhost:5000 en Chrome o Edge. El micrófono funciona en localhost.

## Subirlo a internet (ejemplo con Render)
1. Crea un repositorio en GitHub y sube estos archivos (NO subas tu clave).
2. En render.com: New > Web Service > conecta el repositorio.
3. Build Command:  pip install -r requirements.txt
   Start Command:  gunicorn app:app
4. En Environment agrega:
   - GROQ_API_KEY = tu clave nueva de Groq
   - ACCESS_CODE  = un código que solo tú conozcas (evita que otros gasten tu cuota)
5. Deploy. Render te da una dirección https://... ; el micrófono del navegador exige https.

Railway y servicios parecidos funcionan igual (el Procfile ya está incluido).
Hugging Face Spaces solo sirve Flask si creas un Space de tipo Docker.

## Notas
- Reconocimiento de voz: Chrome/Edge (PC y Android). Safari y Firefox tienen soporte limitado:
  en ese caso usa la caja de texto.
- La memoria de conversación se guarda en el navegador de cada dispositivo, no en el servidor.
- Los planes gratuitos pueden "dormir" el servidor tras un rato sin uso; la primera carga tarda más.

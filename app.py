from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

# Configuración de la API de Epson Connect
CLIENT_ID = "51d888eb62a644da982be6a4b63be62d"  # Reemplaza con tu Client ID
CLIENT_SECRET = "b6lN7ZF1BnvOW8q5ceMHGIPpesQiV0FveYd9W0wAIq7OnvqS7T2KhFix7mIKTeSr"  # Reemplaza con tu Client Secret
PRINTER_EMAIL = "jmi2421vq0j2w5@print.epsonconnect.com"  # Reemplaza con el correo de tu impresora

# Diccionario para gestionar el estado de cada usuario
user_state = {}

def obtener_token_acceso():
    url = "https://api.epsonconnect.com/api/1/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Error al obtener el token de acceso: {response.status_code}")
        return None

def crear_trabajo_impresion(token):
    url = "https://api.epsonconnect.com/api/1/printing"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "printer_email": PRINTER_EMAIL
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al crear el trabajo de impresión: {response.status_code}")
        return None

def subir_archivo_impresion(token, upload_uri, archivo_pdf):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/pdf"
    }
    with open(archivo_pdf, "rb") as f:
        response = requests.put(upload_uri, headers=headers, data=f)
    if response.status_code == 200:
        return True
    else:
        print(f"Error al subir el archivo de impresión: {response.status_code}")
        return False

def ejecutar_impresion(token, job_id):
    url = f"https://api.epsonconnect.com/api/1/printing/{job_id}/execute"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        print(f"Error al ejecutar la impresión: {response.status_code}")
        return False

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From")
    body = request.form.get("Body", "").strip().lower()
    num_media = int(request.form.get("NumMedia", 0))

    if sender in user_state and user_state[sender].get("pending_pdf"):
        if body == "si":
            pdf_url = user_state[sender]["pending_pdf"]
            try:
                r = requests.get(pdf_url)
                if r.status_code == 200:
                    filename = "documento.pdf"
                    with open(filename, "wb") as f:
                        f.write(r.content)
                    if os.path.getsize(filename) == 0:
                        return twiml_response("El archivo PDF descargado está vacío.")
                    token = obtener_token_acceso()
                    if not token:
                        return twiml_response("Error al obtener el token de acceso.")
                    job_info = crear_trabajo_impresion(token)
                    if not job_info:
                        return twiml_response("Error al crear el trabajo de impresión.")
                    upload_uri = job_info["upload_uri"]
                    job_id = job_info["job_id"]
                    if subir_archivo_impresion(token, upload_uri, filename):
                        if ejecutar_impresion(token, job_id):
                            response_msg = "Documento enviado a imprimir."
                        else:
                            response_msg = "Error al ejecutar la impresión."
                    else:
                        response_msg = "Error al subir el archivo de impresión."
                else:
                    response_msg = f"Error al descargar el PDF, status code: {r.status_code}"
            except Exception as e:
                print("Error al descargar el PDF:", e)
                response_msg = "Error al descargar el PDF. Inténtalo de nuevo."
            user_state[sender]["pending_pdf"] = None
        else:
            response_msg = "Operación cancelada. Envía un nuevo PDF si lo deseas."
            user_state[sender]["pending_pdf"] = None
    else:
        if num_media > 0:
            media_type = request.form.get("MediaContentType0", "")
            if "pdf" in media_type.lower():
                pdf_url = request.form.get("MediaUrl0")
                user_state[sender] = {"pending_pdf": pdf_url}
                response_msg = "¿Deseas imprimir el PDF? Responde 'Si' para confirmar."
            else:
                response_msg = "El archivo enviado no es un PDF. Envía un archivo PDF."
        else:
            response_msg = "Envía un archivo PDF para imprimir."

    return twiml_response(response_msg)

def twiml_response(message):
    response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""
    return Response(response, mimetype="application/xml")

if __name__ == "__main__":
    app.run(debug=True)

import requests

# Configuración de la API de Epson Connect
EPSON_API_URL = "https://api.epsonconnect.com/api/1/printing"
CLIENT_ID = "51d888eb62a644da982be6a4b63be62d"
CLIENT_SECRET = "b6lN7ZF1BnvOW8q5ceMHGIPpesQiV0FveYd9W0wAIq7OnvqS7T2KhFix7mIKTeSr"
PRINTER_EMAIL = "jmi2421vq0j2w5@print.epsonconnect.com"

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

def enviar_pdf_a_impresora(pdf_path):
    token = obtener_token_acceso()
    if not token:
        return "Error al obtener el token de acceso."

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    files = {
        "file": (pdf_path, open(pdf_path, "rb"), "application/pdf")
    }

    data = {
        "printer_email": PRINTER_EMAIL,
        "file_name": pdf_path
    }

    response = requests.post(EPSON_API_URL, headers=headers, data=data, files=files)
    if response.status_code == 200:
        return "Documento enviado a imprimir."
    else:
        print(f"Error al enviar el documento a la impresora: {response.status_code}")
        return "Error al enviar el documento a la impresora."

# Uso en tu ruta de Flask
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
                    response_msg = enviar_pdf_a_impresora(filename)
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

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

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

@app.route("/enviar_pdf", methods=["POST"])
def enviar_pdf():
    archivo = request.files.get("archivo")
    if archivo and archivo.filename.endswith(".pdf"):
        archivo_path = f"./{archivo.filename}"
        archivo.save(archivo_path)
        resultado = enviar_pdf_a_impresora(archivo_path)
        return jsonify({"mensaje": resultado})
    else:
        return jsonify({"mensaje": "Por favor, envía un archivo PDF válido."})

if __name__ == "__main__":
    app.run(debug=True)

import urllib3
from flask import Flask, request, Response
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)

# Diccionario para gestionar el estado de cada usuario (para confirmar la impresión)
user_state = {}

# --- Configuración del correo para enviar a Epson Connect ---
EMAIL_USER = "impresoracasaepsonconectar@gmail.com"  # Reemplaza con tu correo
EMAIL_PASS = "mdgnxyxhouvfrate"  # Reemplaza con tu contraseña (o usa variables de entorno para mayor seguridad)
EPSON_EMAIL = "jmi2421vq0j2w5@print.epsonconnect.com"  # La dirección de impresión asignada a tu impresora

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    sender = request.form.get("From")  # Número del remitente
    body = request.form.get("Body", "").strip().lower()
    num_media = int(request.form.get("NumMedia", 0))
    
    print(f"Request received from: {sender}, body: {body}, num_media: {num_media}")

    # Si el usuario ya tiene un PDF pendiente y ahora responde:
    if sender in user_state and user_state[sender].get("pending_pdf"):
        if body == "si":
            pdf_url = user_state[sender]["pending_pdf"]
            try:
                filename = descargar_pdf(pdf_url)
                if filename:
                    print("PDF descargado correctamente.")
                    # Envía el PDF por email a Epson Connect
                    if enviar_email_pdf(filename):
                        response_msg = "Documento enviado a imprimir."
                    else:
                        response_msg = "Error al enviar el documento a imprimir."
                else:
                    response_msg = "Error al descargar el PDF."
                user_state[sender]["pending_pdf"] = None
            except Exception as e:
                print("Error al manejar el PDF:", e)
                response_msg = "Error al manejar el PDF. Inténtalo de nuevo."
                user_state[sender]["pending_pdf"] = None
        else:
            response_msg = "Operación cancelada. Envía un nuevo PDF si lo deseas."
            user_state[sender]["pending_pdf"] = None
    else:
        # Si se adjuntó un archivo
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
    # Respuesta en el formato XML que requiere Twilio (TwiML)
    response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""
    return Response(response, mimetype="application/xml")

def descargar_pdf(pdf_url):
    try:
        http = urllib3.PoolManager()
        pdf_path = 'documento.pdf'
        response = http.request('GET', pdf_url)
        if response.status == 200:
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(response.data)
            if os.path.getsize(pdf_path) > 0:
                with open(pdf_path, "rb") as f:
                    content = f.read(100)
                    print(f"Contenido del PDF (primeros 100 bytes): {content}")
                return pdf_path
            else:
                print("El archivo PDF descargado está vacío.")
                return None
        else:
            print(f"Error al descargar el PDF, status code: {response.status}")
            return None
    except Exception as e:
        print("Error al descargar el PDF:", e)
        return None

def enviar_email_pdf(pdf_path):
    try:
        # Verifica que el archivo no esté vacío antes de adjuntarlo
        if os.path.getsize(pdf_path) == 0:
            print("El archivo PDF está vacío.")
            return False
        
        # Configura el mensaje de email
        msg = MIMEMultipart()
        msg['Subject'] = "Impresión PDF"
        msg['From'] = EMAIL_USER
        msg['To'] = EPSON_EMAIL

        # Adjunta el PDF
        with open(pdf_path, "rb") as f:
            content = f.read()
            part = MIMEApplication(content, _subtype="pdf", Name=os.path.basename(pdf_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
        msg.attach(part)

        # Conecta al servidor SMTP (ejemplo con Gmail)
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EPSON_EMAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error al enviar email:", e)
        return False

if __name__ == "__main__":
    app.run(debug=True)

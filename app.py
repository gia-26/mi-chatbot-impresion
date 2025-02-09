import os
import requests
from twilio.rest import Client
from flask import Flask, request

app = Flask(__name__)

# Configura tus credenciales de Twilio
TWILIO_ACCOUNT_SID = 'AC5f45411a799b46ee424835624e325da0'
TWILIO_AUTH_TOKEN = '53f98ecc4e20fb38eaed41f4f8b50b6f'
TWILIO_PHONE_NUMBER = 'whatsapp:+5214931131012'  # Número de WhatsApp de Twilio

# Configura tus credenciales de Epson Connect
PRINTER_EMAIL = 'jmi2421vq0j2w5@print.epsonconnect.com'
CLIENT_ID = '51d888eb62a644da982be6a4b63be62d'
CLIENT_SECRET = 'b6lN7ZF1BnvOW8q5ceMHGIPpesQiV0FveYd9W0wAIq7OnvqS7T2KhFix7mIKTeSr'

# Inicializa el cliente de Twilio
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtiene el SID del mensaje entrante
    message_sid = request.form['MessageSid']
    
    # Recupera el mensaje de Twilio
    message = twilio_client.messages(message_sid).fetch()
    
    # Verifica si el mensaje contiene un archivo multimedia
    if message.media_count > 0:
        # Obtiene la URL del archivo multimedia
        media_url = message.media.list()[0].uri
        media_url = f'https://api.twilio.com{media_url}'
        
        # Descarga el archivo PDF
        response = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if response.status_code == 200:
            # Guarda el archivo en el servidor
            with open('received_file.pdf', 'wb') as f:
                f.write(response.content)
            
            # Envía el archivo a la impresora Epson
            send_to_printer('received_file.pdf')
            return 'Archivo recibido y enviado a la impresora', 200
        else:
            return 'Error al descargar el archivo', 500
    else:
        return 'No se recibió archivo multimedia', 400

def send_to_printer(file_path):
    try:
        # Envía el archivo PDF a la impresora Epson
        job_id = epson_client.printer.print(file_path)
        print(f'Impresión iniciada con Job ID: {job_id}')
    except Exception as e:
        print(f'Error al enviar a la impresora: {e}')

if __name__ == '__main__':
    app.run(debug=True)

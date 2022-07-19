import requests
import smtplib
import ssl
from email.message import EmailMessage
import geocoder
from sys import exit
import json
import os.path


if __name__ == "__main__":

    def ler_json(a):
        with open("infos.json", "r") as f:
            return json.load(f)[a]

    def create_file():
        api_key = input("Digite sua chave da API: ")
        sender_email = input("Digite o email que ENVIARÁ o alerta: ")
        password = input("Digite a SENHA do email que enviará o alerta: ")
        receiver_email = input("Digite o email que RECEBERÁ o alerta: ")

        estrutura = {
            "api_key": api_key,
            "sender_email": sender_email,
            "password": password,
            "receiver_email": [receiver_email],
        }

        with open("infos.json", "w") as f:
            json.dump(estrutura, f, ensure_ascii=False, indent=4)

    if not os.path.isfile('infos.json'):
        create_file()

    API_KEY = ler_json("api_key")  # Chave da API para consulta
    BASE_URL = "https://api.openweathermap.org/data/2.5/onecall"  # URL base para request das informações climáticas do dia
    GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/reverse"  # URL base para request da localização geográfica (latitude e longitude) da cidade onde será criado o alerta

    # Obtenção das coordenadas de latitude e longitude
    g = geocoder.ip("me")
    lat, lon = g.latlng
    request_geo = f"{GEOCODING_URL}?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"  # Complemento para o request da localização geográfica
    response_geo = requests.get(request_geo)

    if response_geo.status_code == 200:
        city = response_geo.json()[0]["name"]
    else:
        print("Ocorreu um erro.")
        exit()

    # Request da previsão do tempo do dia (excluindo previsão atual, por minuto e por hora), no sistema métrico e em português
    request_url = f"{BASE_URL}?lat={lat}&lon={lon}&units=metric&lang=pt_br&exclude=current,minutely,hourly&appid={API_KEY}"
    response = requests.get(request_url)

    if response.status_code == 200:
        data = response.json()
        try:
            alertas = data["alerts"][0]["description"]  # Isolando a descrição do alerta
            send = True
        except:
            send = False
            pass
    else:
        print("Ocorreu um erro.")
        exit()

    if send:
        subject = f"Alerta de tempestade em {city.capitalize()}!"  # Mensagem que aparecerá como Assunto do email
        body = alertas
        sender_email = ler_json("sender_email")  # Email que enviará o alerta
        receiver_email = ler_json("receiver_email")  # Email que receberá o alerta
        password = ler_json("password")  # Senha do email que enviará o alerta

        message = EmailMessage()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        html = f"""
        <html>
            <body>
                <h1>{subject}</h1>
                <p>{body}</p>
            </body>
        </html>
        """

        message.add_alternative(html, subtype="html")

        context = ssl.create_default_context()
        print("Enviando Email")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        print("Email Enviado")
    else:
        print("Não há alertas hoje para esta localização.")

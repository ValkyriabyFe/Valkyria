import time
import requests
import json
from datetime import datetime
from valkyriabot import interpretar_mensagem
from inteligencia import carregar_memoria

TOKEN = "7791777972:AAG1TBho1bSMEKGBncWz3q7a5vHBvRlGjfl"
ID_USUARIO_AUTORIZADO = 1319982843
URL = f"https://api.telegram.org/bot{TOKEN}/"

def enviar_mensagem(texto):
    requests.post(URL + "sendMessage", json={"chat_id": ID_USUARIO_AUTORIZADO, "text": texto})

def obter_atualizacoes(offset=None):
    params = {"timeout": 100, "offset": offset}
    resp = requests.get(URL + "getUpdates", params=params)
    return resp.json()

def main():
    memoria = carregar_memoria()
    ultimo_update_id = None

    while True:
        atualizacoes = obter_atualizacoes(ultimo_update_id)
        for resultado in atualizacoes.get("result", []):
            mensagem = resultado["message"]
            chat_id = mensagem["chat"]["id"]
            texto = mensagem.get("text", "")
            update_id = resultado["update_id"]

            if chat_id == ID_USUARIO_AUTORIZADO and texto:
                resposta = interpretar_mensagem(texto, memoria)
                enviar_mensagem(resposta)
            
            ultimo_update_id = update_id + 1
        time.sleep(2)

if _name_ == "_main_":
    main()

import telebot
import os

# Token do bot
FICHA = '7791777972:AAG1TBho1bSMEKGBncWz3q7a5vHBvRlGjfl'
robô = telebot.TeleBot(FICHA)

@robô.message_handler(commands=['começar', 'iniciar'])
def enviar_boas_vindas(mensagem):
    robô.send_message(mensagem.chat.id, "Valkyria online. Pronta para executar comandos.")

@robô.message_handler(func=lambda m: True)
def responder_comando(mensagem):
    texto = mensagem.text.lower()

    if 'status' in texto:
        resposta = "Valkyria está ativa e rodando com monitoramento."
    elif 'binance' in texto:
        resposta = "Conectado à conta real da Binance."
    elif 'ganhos' in texto:
        resposta = "Últimos ganhos e perdas estão sendo analisados."
    else:
        resposta = "Comando não reconhecido. Envie: status, binance, ganhos..."

    robô.send_message(mensagem.chat.id, resposta)

robô.polling()

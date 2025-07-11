import telebot
import os

# Token do bot
TOKEN = '6944631209:AAEcmjYOgydvZ0XoAQ9zMRDDElJ5mfxOils'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'iniciar'])
def send_welcome(message):
    bot.reply_to(message, "ValKyria online. Pronta para executar comandos.")

@bot.message_handler(func=lambda m: True)
def responder_comando(message):
    texto = message.text.lower()

    if 'status' in texto:
        resposta = "ValKyria está ativa e rodando com monitoramento."
    elif 'binance' in texto:
        resposta = "Conectada à conta real da Binance."
    elif 'ganhos' in texto:
        resposta = "Últimos ganhos e perdas estão sendo analisados."
    else:
        resposta = "Comando não reconhecido. Tente: status, binance, ganhos..."

    bot.reply_to(message, resposta)

# ESSENCIAL PARA FUNCIONAR
bot.polling(none_stop=True)

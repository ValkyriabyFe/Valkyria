import telebot
import subprocess

# TOKEN e ID já configurados
TOKEN = "6928231485:AAHnKDcCC40sVdXQhgnKWhZV_bWD_g3mO1Q"
ADMIN_ID = 5910676333

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['status'])
def status(message):
    if message.chat.id == ADMIN_ID:
        try:
            result = subprocess.check_output("systemctl status valkyria.service", shell=True).decode()
            bot.reply_to(message, f"Status:\n{result}")
        except Exception as e:
            bot.reply_to(message, f"Erro ao obter status:\n{e}")
    else:
        bot.reply_to(message, "Acesso negado.")

@bot.message_handler(commands=['reiniciar'])
def reiniciar(message):
    if message.chat.id == ADMIN_ID:
        try:
            subprocess.call("systemctl restart valkyria.service", shell=True)
            bot.reply_to(message, "Valkyria reiniciada com sucesso.")
        except Exception as e:
            bot.reply_to(message, f"Erro ao reiniciar:\n{e}")
    else:
        bot.reply_to(message, "Acesso negado.")

@bot.message_handler(commands=['log'])
def logs(message):
    if message.chat.id == ADMIN_ID:
        try:
            log = subprocess.check_output("tail -n 30 /var/log/syslog | grep valkyria", shell=True).decode()
            bot.reply_to(message, f"Últimos logs:\n{log}")
        except Exception as e:
            bot.reply_to(message, f"Erro ao puxar logs:\n{e}")
    else:
        bot.reply_to(message, "Acesso negado.")

@bot.message_handler(func=lambda m: True)
def fallback(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "Comandos:\n/status\n/reiniciar\n/log")
    else:
        bot.reply_to(message, "Acesso restrito.")

bot.polling()

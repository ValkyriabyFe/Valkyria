import time
import datetime

def log(msg):
    hora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{hora}] {msg}")

log("ValKyria iniciada com sucesso.")
log("Monitorando o mercado em tempo real...")

while True:
    # Aqui futuramente entra a análise de candles, volume e IA decisora
    log("📊 Nenhuma entrada detectada. Aguardando novo sinal...")
    time.sleep(10)

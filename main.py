[13:49, 07/07/2025] Felipe Weissmann: import time
import datetime
import random

def log(msg):
    hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{hora}] {msg}")

log("ValKyria iniciada com sucesso.")
log("Monitorando o mercado em tempo real...")

while True:
    # Simulação de entrada de sinal (vamos trocar depois por candles reais)
    chance_de_entrada = random.randint(1, 100)

    if chance_de_entrada > 97:  # Simula entrada aleatória
        log(" SINAL DETECTADO: Condição de entrada confirmada.")
        log(" Ordem de COMPRA executada com sucesso. Aguardando evolução da operação...")
        break

    log(" Nenhuma entrada detectada. Aguardando novo sinal...")
    time.sleep(10)
[14:31, 07/07/2025] Felipe Weissmann: import os
import time
import json
import datetime
from decimal import Decimal
from binance.client import Client
from binance.enums import *

# === CHAVES DE ACESSO via variáveis de ambiente ===
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)

# === CONFIGURAÇÕES ===
pares = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
intervalos = [Client.KLINE_INTERVAL_1MINUTE, Client.KLINE_INTERVAL_5MINUTE, Client.KLINE_INTERVAL_15MINUTE]
fator_risco_inicial = Decimal('0.10')
stop_loss_pct = Decimal('0.97')
take_profit_pct = Decimal('1.04')
historico_resultados = {}

def log(msg):
    hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{hora}] {msg}")

def tendencia_positiva(symbol):
    positivos = 0
    for intervalo in intervalos:
        candles = client.get_klines(symbol=symbol, interval=intervalo, limit=5)
        if not candles or len(candles) < 2:
            continue
        fechamento_atual = float(candles[-1][4])
        fechamento_anterior = float(candles[-2][4])
        volume_atual = float(candles[-1][5])
        volume_anterior = float(candles[-2][5])
        if fechamento_atual > fechamento_anterior and volume_atual > volume_anterior:
            positivos += 1
    return positivos >= 2

def ajustar_risco(par, resultado):
    historico_resultados.setdefault(par, [])
    historico_resultados[par].append(resultado)

    if len(historico_resultados[par]) > 10:
        historico_resultados[par].pop(0)

    taxa_acerto = historico_resultados[par].count('win') / len(historico_resultados[par])
    if taxa_acerto > 0.6:
        return min(fator_risco_inicial + Decimal('0.01'), Decimal('0.20'))
    elif taxa_acerto < 0.4:
        return max(fator_risco_inicial - Decimal('0.01'), Decimal('0.02'))
    else:
        return fator_risco_inicial

def calcular_quantidade(symbol, saldo_usdt, fator_risco):
    preco = float(client.get_symbol_ticker(symbol=symbol)['price'])
    quantidade = float((Decimal(saldo_usdt) * fator_risco) / Decimal(preco))
    info = client.get_symbol_info(symbol)
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step = float(f['stepSize'])
            return round(quantidade - (quantidade % step), 6)
    return round(quantidade, 6)

def operar(symbol):
    saldo = client.get_asset_balance(asset='USDT')
    saldo_disponivel = Decimal(saldo['free'])
    if saldo_disponivel < 10:
        log(f"Saldo insuficiente para operar: {saldo_disponivel}")
        return

    fator_risco = ajustar_risco(symbol, 'neutro')
    quantidade = calcular_quantidade(symbol, saldo_disponivel, fator_risco)
    preco_entrada = float(client.get_symbol_ticker(symbol=symbol)['price'])

    try:
        ordem = client.order_market_buy(symbol=symbol, quantity=quantidade)
        log(f"COMPRA em {symbol} | Quantidade: {quantidade} | Preço: {preco_entrada:.2f}")
        log(json.dumps(ordem, indent=2))
    except Exception as e:
        log(f"Erro ao comprar: {str(e)}")
        return

    while True:
        try:
            preco_atual = float(client.get_symbol_ticker(symbol=symbol)['price'])
            if preco_atual <= preco_entrada * float(stop_loss_pct):
                client.order_market_sell(symbol=symbol, quantity=quantidade)
                log(f"STOP em {symbol}: {preco_atual:.2f}")
                ajustar_risco(symbol, 'loss')
                break
            elif preco_atual >= preco_entrada * float(take_profit_pct):
                client.order_market_sell(symbol=symbol, quantity=quantidade)
                log(f"TAKE em {symbol}: {preco_atual:.2f}")
                ajustar_risco(symbol, 'win')
                break
            else:
                log(f"Aguardando {symbol}: {preco_atual:.2f}")
                time.sleep(10)
        except Exception as e:
            log(f"Erro monitorando {symbol}: {str(e)}")
            time.sleep(10)

# === LOOP PRINCIPAL ===
log("ValKyria 3.0 iniciada com sucesso.")

while True:
    try:
        for par in pares:
            if tendencia_positiva(par):
                log(f"Tendência positiva em {par}. Operando...")
                operar(par)
            else:
                log(f"Nenhum sinal em {par}.")
        time.sleep(5)
    except Exception as e:
        log(f"Erro geral: {str(e)}")
        time.sleep(30)

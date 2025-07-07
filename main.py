import os
import time
import json
import datetime
from decimal import Decimal
from binance.client import Client
from binance.enums import *

# === CONFIGURAÇÃO DA BINANCE ===
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)

# === CONFIGURAÇÕES ===
pares = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
intervalos = [Client.KLINE_INTERVAL_1MINUTE, Client.KLINE_INTERVAL_5MINUTE, Client.KLINE_INTERVAL_15MINUTE]
fator_risco_inicial = Decimal('0.10')  # Começa com 10% do saldo
stop_loss_pct = Decimal('0.97')        # 3% de perda
take_profit_pct = Decimal('1.04')      # 4% de lucro
historico_resultados = {}

# === LOG FORMATADO ===
def log(msg):
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] {msg}")

# === ANÁLISE DE TENDÊNCIA E VOLUME EM MÚLTIPLOS TEMPOS ===
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

# === AJUSTE DE RISCO POR PAR (AUTOAPRENDIZADO SIMPLES) ===
def ajustar_risco(par, resultado):
    global fator_risco_inicial
    historico_resultados.setdefault(par, [])
    historico_resultados[par].append(resultado)
    if len(historico_resultados[par]) > 10:
        historico_resultados[par].pop(0)
    taxa = historico_resultados[par].count('win') / len(historico_resultados[par])
    if taxa > 0.6:
        return min(fator_risco_inicial + Decimal('0.01'), Decimal('0.20'))
    elif taxa < 0.4:
        return max(fator_risco_inicial - Decimal('0.01'), Decimal('0.02'))
    return fator_risco_inicial

# === CÁLCULO AUTOMÁTICO DE QUANTIDADE ===
def calcular_quantidade(symbol, saldo_usdt, fator_risco):
    preco = float(client.get_symbol_ticker(symbol=symbol)['price'])
    quantidade = float((Decimal(saldo_usdt) * fator_risco) / Decimal(preco))
    info = client.get_symbol_info(symbol)
    for f in info['filters']:
        if f['filterType'] == 'LOT_SIZE':
            step = float(f['stepSize'])
            return round(quantidade - (quantidade % step), 6)
    return round(quantidade, 6)

# === EXECUTA OPERAÇÃO REAL E MONITORA ATÉ SAÍDA ===
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
        log(f"Compra executada em {symbol}. Preço: {preco_entrada:.2f}")
        log(json.dumps(ordem, indent=2))
    except Exception as e:
        log(f"Erro na compra: {str(e)}")
        return

    while True:
        try:
            preco_atual = float(client.get_symbol_ticker(symbol=symbol)['price'])
            if preco_atual <= preco_entrada * float(stop_loss_pct):
                client.order_market_sell(symbol=symbol, quantity=quantidade)
                log(f"STOP acionado em {symbol}. Preço: {preco_atual:.2f}")
                ajustar_risco(symbol, 'loss')
                break
            elif preco_atual >= preco_entrada * float(take_profit_pct):
                client.order_market_sell(symbol=symbol, quantity=quantidade)
                log(f"TAKE atingido em {symbol}. Preço: {preco_atual:.2f}")
                ajustar_risco(symbol, 'win')
                break
            else:
                log(f"Aguardando: {preco_atual:.2f} ({symbol})")
                time.sleep(15)
        except Exception as e:
            log(f"Erro ao monitorar {symbol}: {str(e)}")
            time.sleep(15)

# === LOOP CONTÍNUO ===
log("ValKyria FINAL 100% iniciada com sucesso.")
while True:
    try:
        for par in pares:
            if tendencia_positiva(par):
                log(f"Tendência positiva detectada em {par}. Executando operação...")
                operar(par)
            else:
                log(f"Nenhuma entrada em {par}.")
        time.sleep(5)
    except Exception as e:
        log(f"Erro geral: {str(e)}")
        time.sleep(30)

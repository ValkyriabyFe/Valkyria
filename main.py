import ccxt
import time
import pandas as pd
import numpy as np
import ta
import talib
import json
from datetime import datetime
import os
from inteligencia import ajustar_score

# === CONFIGURAÇÕES ===
api_key = 'SUA_API_KEY'
api_secret = 'SUA_API_SECRET'

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

memory_file = 'valkyria_memory.json'
if not os.path.exists(memory_file):
    with open(memory_file, 'w') as f:
        json.dump([], f)

usdt_balance = lambda: float(exchange.fetch_balance()['total']['USDT'])

# === SALVAR HISTÓRICO ===
def save_memory(entry):
    try:
        with open(memory_file, 'r') as f:
            data = json.load(f)
    except:
        data = []
    data.append(entry)
    with open(memory_file, 'w') as f:
        json.dump(data, f, indent=4)

# === OBTÉM OS 20 MAIORES PARES POR VOLUME ===
def get_top_pairs(limit=20):
    try:
        tickers = exchange.fetch_tickers()
        spot_usdt = [s for s in tickers if s.endswith('/USDT') and '_CM' not in s and 'UP/' not in s and 'DOWN/' not in s]
        volumes = [(s, tickers[s]['quoteVolume']) for s in spot_usdt if tickers[s]['quoteVolume']]
        sorted_volumes = sorted(volumes, key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_volumes[:limit]]
    except:
        return []

# === PUXA DADOS DE MERCADO ===
def fetch_ohlcv(symbol, timeframe, limit=100):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except:
        return []

# === DETECÇÃO DE PADRÕES GRÁFICOS ===
def detect_patterns(df):
    patterns = [
        talib.CDLENGULFING, talib.CDLHARAMI, talib.CDLMORNINGSTAR, talib.CDLSHOOTINGSTAR,
        talib.CDLDOJI, talib.CDL3INSIDE, talib.CDLPIERCING, talib.CDLINVERTEDHAMMER, talib.CDLHAMMER
    ]
    o = df['open'].values
    h = df['high'].values
    l = df['low'].values
    c = df['close'].values
    for pattern_func in patterns:
        result = pattern_func(o, h, l, c)
        if result[-1] != 0:
            return pattern_func._name_
    return ''

# === ANÁLISE COMPLETA DO PAR ===
def analyze_pair(symbol):
    data_1m = fetch_ohlcv(symbol, '1m')
    data_5m = fetch_ohlcv(symbol, '5m')
    data_15m = fetch_ohlcv(symbol, '15m')
    data_1h = fetch_ohlcv(symbol, '1h')

    if not data_1m or not data_5m or not data_15m or not data_1h:
        return None

    df = pd.DataFrame(data_1m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['ema'] = ta.trend.ema_indicator(df['close'], window=20)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['macd'] = ta.trend.macd_diff(df['close'])

    pattern = detect_patterns(df)

    score = 0
    if df['volume'].iloc[-1] > df['volume'].mean() * 1.5:
        score += 1
    if df['close'].iloc[-1] > df['ema'].iloc[-1]:
        score += 1
    if df['macd'].iloc[-1] > 0:
        score += 1
    if 50 < df['rsi'].iloc[-1] < 70:
        score += 1
    if pattern:
        score += 1

    # IA inteligente ajusta score com base em histórico e livros
    score = ajustar_score(symbol, score, pattern, df)

    return score, df['close'].iloc[-1], pattern, df

# === EXECUTA ORDEM ===
def place_order(symbol, price, side, usdt_value):
    try:
        qty = round(usdt_value / price, 6)
        order = exchange.create_order(symbol=symbol, type='market', side=side, amount=qty)
        print(f"[ORDEM] {side.upper()} {symbol} | Qty: {qty} | Preço: {price:.4f}")
        return order
    except Exception as e:
        print(f"[ERRO ORDEM] {e}")
        return None

# === LOOP PRINCIPAL ===
in_position = False
symbol_in_trade = ''
entry_price = 0
stop_loss = 0
take_profit = 0
max_price = 0
best_pattern = ''

while True:
    try:
        if not in_position:
            top_pairs = get_top_pairs()
            best_score = 0
            best_pair = ''
            best_price = 0

            for pair in top_pairs:
                result = analyze_pair(pair)
                if result:
                    score, price, pattern, df = result
                    if score > best_score:
                        best_score = score
                        best_pair = pair
                        best_price = price
                        best_pattern = pattern

            if best_score >= 4:
                balance = usdt_balance()
                risk_percent = 0.05 + best_score * 0.01
                order_value = balance * risk_percent
                order = place_order(best_pair, best_price, 'buy', order_value)

                if order:
                    in_position = True
                    symbol_in_trade = best_pair
                    entry_price = best_price
                    stop_loss = entry_price * 0.985
                    take_profit = entry_price * 1.03
                    max_price = entry_price

        else:
            ticker = exchange.fetch_ticker(symbol_in_trade)
            last_price = ticker['last']
            volume_now = ticker['quoteVolume']
            avg_volume = ticker.get('average', volume_now)

            if last_price > max_price:
                max_price = last_price
                stop_loss = max(stop_loss, max_price * 0.98)  # trailing

            if last_price <= stop_loss or last_price >= take_profit or volume_now < avg_volume * 0.5:
                order = place_order(symbol_in_trade, last_price, 'sell', usdt_balance())
                if order:
                    print(f"[SAÍDA] {symbol_in_trade} | Preço: {last_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    result = 'gain' if last_price > entry_price else 'loss'
                    save_memory({
                        'symbol': symbol_in_trade,
                        'entry': entry_price,
                        'exit': last_price,
                        'result': result,
                        'pattern': best_pattern,
                        'time': datetime.utcnow().isoformat()
                    })
                    in_position = False
                    symbol_in_trade = ''
                    entry_price = 0

        time.sleep(5)

    except Exception as e:
        print(f"[ERRO LOOP] {e}")
        time.sleep(5)

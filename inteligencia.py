import json
import pandas as pd
import numpy as np
from datetime import datetime

memory_file = 'valkyria_memory.json'

# === Score por histórico de par/padrão ===
def ajustar_score_por_historico(symbol, score, pattern):
    try:
        with open(memory_file, 'r') as f:
            historico = json.load(f)
    except:
        return score

    ganhos = 0
    perdas = 0
    padrao_bonus = 0

    for r in historico:
        if r['symbol'] == symbol:
            if r['result'] == 'gain':
                ganhos += 1
            elif r['result'] == 'loss':
                perdas += 1
            if pattern and pattern in r.get('pattern', '') and r['result'] == 'gain':
                padrao_bonus += 1

    total = ganhos + perdas
    taxa_sucesso = ganhos / total if total > 0 else 0.5
    ajuste = 0

    if taxa_sucesso > 0.7:
        ajuste += 1
    elif taxa_sucesso < 0.3:
        ajuste -= 1

    if padrao_bonus >= 3:
        ajuste += 1

    return score + ajuste

# === Score global por padrão (independente do par) ===
def ajustar_score_por_padrao_global(score, pattern):
    try:
        with open(memory_file, 'r') as f:
            historico = json.load(f)
    except:
        return score

    total = 0
    ganhos = 0

    for r in historico:
        if r.get('pattern') == pattern:
            total += 1
            if r['result'] == 'gain':
                ganhos += 1

    if total == 0:
        return score

    taxa = ganhos / total
    if taxa > 0.7:
        return score + 1
    elif taxa < 0.3:
        return score - 1
    return score

# === Análise técnica clássica (livros) ===
def ajustar_score_por_livros_tecnicos(score, df):
    ajuste = 0

    # 1. Divergência RSI
    rsi = df['rsi'].iloc[-1]
    price_diff = df['close'].iloc[-1] - df['close'].iloc[-5]
    rsi_diff = rsi - df['rsi'].iloc[-5]

    if price_diff > 0 and rsi_diff < 0:
        ajuste -= 1  # Divergência de baixa
    elif price_diff < 0 and rsi_diff > 0:
        ajuste += 1  # Divergência de alta

    # 2. Tendência por EMA
    ema = df['ema'].iloc[-1]
    if df['close'].iloc[-1] > ema and df['close'].mean() > ema:
        ajuste += 1
    elif df['close'].iloc[-1] < ema and df['close'].mean() < ema:
        ajuste += 1

    # 3. Candle de força + volume
    candle = df['close'].iloc[-1] - df['open'].iloc[-1]
    avg_candle = (df['close'] - df['open']).mean()
    volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].mean()

    if abs(candle) > abs(avg_candle) * 1.5 and volume > avg_volume * 1.5:
        ajuste += 1

    # 4. Lateralização (mercado preso)
    maximo = df['high'].iloc[-15:].max()
    minimo = df['low'].iloc[-15:].min()
    spread = maximo - minimo
    if spread < df['close'].iloc[-1] * 0.005:
        ajuste -= 1

    return score + ajuste

# === Horário de operação (momentum global) ===
def ajustar_score_por_horario(score):
    hora_utc = datetime.utcnow().hour
    if 12 <= hora_utc <= 17:
        return score + 1  # Horário de maior volume global
    elif 0 <= hora_utc <= 3:
        return score - 1  # Baixa liquidez
    return score

# === Função principal chamada no main.py ===
def ajustar_score(symbol, score, pattern, df):
    score += ajustar_score_por_historico(symbol, 0, pattern) * 1.0
    score += ajustar_score_por_padrao_global(0, pattern) * 1.2
    score += ajustar_score_por_livros_tecnicos(0, df) * 1.5
    score += ajustar_score_por_horario(0) * 0.5
    return max(0, score)

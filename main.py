import time
import requests
import pandas as pd
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

# SUA CHAVE DO RAPIDAPI
RAPIDAPI_KEY = "296ad269ddmsh9a51510151a5714p118b65jsn9ac449b7b4d4"

def get_vix_price():
    """Preço atual do VIX via TradingView (1m)."""
    vix = TA_Handler(
        symbol="VIX",
        screener="america",
        exchange="TVC",
        interval=Interval.INTERVAL_1_MINUTE
    )
    data = vix.get_analysis()
    return data.indicators["close"]


def get_vix_history():
    """Candles de 1 minuto do VIX via Yahoo Finance (RapidAPI, apidojo)."""

    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-charts"

    querystring = {
        "symbol": "^VIX",
        "interval": "1m",
        "range": "2h"   # ~120 candles de 1m
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
    }

    r = requests.get(url, headers=headers, params=querystring).json()

    try:
        timestamps = r["chart"]["result"][0]["timestamp"]
        closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    except Exception:
        print("Erro ao obter histórico:", r)
        return None

    df = pd.DataFrame({
        "timestamp": [datetime.fromtimestamp(t) for t in timestamps],
        "close": closes
    })

    df = df.dropna()
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def variacao(atual, passado):
    if passado == 0:
        return 0.0
    return (atual - passado) / passado * 100


def process_vix():
    print("\n--- COLETANDO DADOS DO VIX ---")
    agora = datetime.now().isoformat(timespec="seconds")
    print("Horário:", agora)

    # Preço atual (1m) via TradingView
    preco_atual = get_vix_price()
    print("Preço atual (1m):", preco_atual)

    # Histórico 1m via Yahoo Finance
    dados = get_vix_history()
    if dados is None or len(dados) < 60:
        print("Histórico insuficiente.")
        return

    # Reamostrar para candles de 5m, 15m, 30m, 60m
    df = dados.copy()
    df.set_index("timestamp", inplace=True)

    # Reamostragem: último fechamento do período
    close_5m = df["close"].resample("5T").last()
    close_15m = df["close"].resample("15T").last()
    close_30m = df["close"].resample("30T").last()
    close_60m = df["close"].resample("60T").last()

    # Pega o candle FECHADO mais recente de cada timeframe
    # (descarta candle parcial em formação)
    if len(close_5m) < 2 or len(close_15m) < 2 or len(close_30m) < 2 or len(close_60m) < 2:
        print("Ainda não há candles suficientes em algum timeframe.")
        return

    preco_5m_close = close_5m.iloc[-2]   # último candle fechado de 5m
    preco_15m_close = close_15m.iloc[-2] # último candle fechado de 15m
    preco_30m_close = close_30m.iloc[-2] # último candle fechado de 30m
    preco_60m_close = close_60m.iloc[-2] # último candle fechado de 60m

    var_5 = variacao(preco_atual, preco_5m_close)
    var_15 = variacao(preco_atual, preco_15m_close)
    var_30 = variacao(preco_atual, preco_30m_close)
    var_60 = variacao(preco_atual, preco_60m_close)

    print("\n--- COMPARAÇÃO COM FECHAMENTO DE CANDLES ---")
    print(f"Atual (1m):       {preco_atual:.4f}")
    print(f"Fech. 5m atrás:   {preco_5m_close:.4f}  | var vs atual: {var_5:.2f}%")
    print(f"Fech. 15m atrás:  {preco_15m_close:.4f} | var vs atual: {var_15:.2f}%")
    print(f"Fech. 30m atrás:  {preco_30m_close:.4f} | var vs atual: {var_30:.2f}%")
    print(f"Fech. 60m atrás:  {preco_60m_close:.4f} | var vs atual: {var_60:.2f}%")

    # Registrar tudo em CSV
    registro = {
        "timestamp": agora,
        "vix_atual_1m": preco_atual,
        "vix_close_5m": preco_5m_close,
        "vix_close_15m": preco_15m_close,
        "vix_close_30m": preco_30m_close,
        "vix_close_60m": preco_60m_close,
        "var_vs_5m_pct": var_5,
        "var_vs_15m_pct": var_15,
        "var_vs_30m_pct": var_30,
        "var_vs_60m_pct": var_60,
    }

    df_log = pd.DataFrame([registro])
    df_log.to_csv("vix_log.csv", mode="a", header=False, index=False)

    print("Registro salvo.")


def main():
    print("Monitor de VIX iniciado na Railway...")
    while True:
        process_vix()
        time.sleep(60)


if __name__ == "__main__":
    main()

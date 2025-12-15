import time
import requests
import pandas as pd
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

# SUA CHAVE DO RAPIDAPI
RAPIDAPI_KEY = "296ad269ddmsh9a51510151a5714p118b65jsn9ac449b7b4d4"


def get_vix_price():
    """Preço atual do VIX via TradingView."""
    vix = TA_Handler(
        symbol="VIX",
        screener="america",
        exchange="TVC",
        interval=Interval.INTERVAL_1_MINUTE
    )
    data = vix.get_analysis()
    return data.indicators["close"]


def get_vix_history():
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-charts"

    querystring = {
        "symbol": "^VIX",
        "interval": "1m",
        "range": "2h"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
    }

    r = requests.get(url, headers=headers, params=querystring).json()

    try:
        timestamps = r["chart"]["result"][0]["timestamp"]
        closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    except Exception as e:
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
    return (atual - passado) / passado * 100


def process_vix():
    print("\n--- COLETANDO DADOS DO VIX ---")
    agora = datetime.now().isoformat(timespec="seconds")
    print("Horário:", agora)

    preco_atual = get_vix_price()
    print("Preço atual:", preco_atual)

    dados = get_vix_history()
    if dados is None or len(dados) < 60:
        print("Histórico insuficiente.")
        return

    preco_5 = dados.iloc[-5]["close"]
    preco_15 = dados.iloc[-15]["close"]
    preco_30 = dados.iloc[-30]["close"]
    preco_60 = dados.iloc[-60]["close"]

    var_5 = variacao(preco_atual, preco_5)
    var_15 = variacao(preco_atual, preco_15)
    var_30 = variacao(preco_atual, preco_30)
    var_60 = variacao(preco_atual, preco_60)

    print("\n--- COMPARAÇÃO DE FECHAMENTOS ---")
    print(f"Atual (1min): {preco_atual}")
    
    print(f"5 min atrás:  {preco_5}  | variação: {var_5:.2f}%")
    print(f"15 min atrás: {preco_15} | variação: {var_15:.2f}%")
    print(f"30 min atrás: {preco_30} | variação: {var_30:.2f}%")
    print(f"60 min atrás: {preco_60} | variação: {var_60:.2f}%")

    registro = {
        "timestamp": agora,
        "vix_atual": preco_atual,
        "vix_5min": preco_5,
        "vix_15min": preco_15,
        "vix_30min": preco_30,
        "vix_60min": preco_60,
        "var_5min_pct": var_5,
        "var_15min_pct": var_15,
        "var_30min_pct": var_30,
        "var_60min_pct": var_60,
    }

    df = pd.DataFrame([registro])
    df.to_csv("vix_log.csv", mode="a", header=False, index=False)

    print("Registro salvo.")


def main():
    print("Monitor de VIX iniciado na Railway...")
    while True:
        process_vix()
        time.sleep(60)


if __name__ == "__main__":
    main()

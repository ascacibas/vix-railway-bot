import time
from datetime import datetime
import pandas as pd
from tradingview_ta import TA_Handler, Interval


def get_vix_price():
    """Retorna o preço atual do VIX."""
    vix = TA_Handler(
        symbol="VIX",
        screener="america",
        exchange="TVC",
        interval=Interval.INTERVAL_1_MINUTE
    )
    data = vix.get_analysis()
    return data.indicators["close"]


def get_vix_history():
    """Retorna candles históricos usando TradingView."""
    vix = TA_Handler(
        symbol="VIX",
        screener="america",
        exchange="TVC",
        interval=Interval.INTERVAL_1_MINUTE
    )
    data = vix.get_analysis()
    candles = data.indicators.get("Recommend.Other", None)

    # tradingview_ta não fornece candles diretamente,
    # então usamos uma técnica alternativa:
    # pegamos o histórico via "oscillators" e "moving averages"
    # mas isso não dá candles reais.
    # Então vamos usar uma API pública alternativa:
    import requests

    url = "https://query1.finance.yahoo.com/v8/finance/chart/^VIX?interval=1m&range=2h"
    r = requests.get(url).json()

    timestamps = r["chart"]["result"][0]["timestamp"]
    closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]

    df = pd.DataFrame({
        "timestamp": timestamps,
        "close": closes
    })

    return df


def variacao(atual, passado):
    return (atual - passado) / passado * 100


def process_vix():
    print("\n--- COLETANDO DADOS DO VIX ---")
    agora = datetime.now().isoformat(timespec="seconds")
    print(f"Horário: {agora}")

    preco_atual = get_vix_price()
    print(f"Preço atual do VIX: {preco_atual}")

    dados = get_vix_history()

    if len(dados) < 60:
        print("Histórico insuficiente.")
        return

    dados = dados.sort_values("timestamp")

    preco_5 = dados.iloc[-5]["close"]
    preco_15 = dados.iloc[-15]["close"]
    preco_30 = dados.iloc[-30]["close"]
    preco_60 = dados.iloc[-60]["close"]

    var_5 = variacao(preco_atual, preco_5)
    var_15 = variacao(preco_atual, preco_15)
    var_30 = variacao(preco_atual, preco_30)
    var_60 = variacao(preco_atual, preco_60)

    print("\n--- VARIAÇÕES ---")
    print(f"Variação 5 min:  {var_5:.2f}%")
    print(f"Variação 15 min: {var_15:.2f}%")
    print(f"Variação 30 min: {var_30:.2f}%")
    print(f"Variação 60 min: {var_60:.2f}%")

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

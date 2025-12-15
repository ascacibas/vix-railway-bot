import time
import requests
import pandas as pd
from datetime import datetime
from tradingview_ta import TA_Handler, Interval


API_KEY = "J77M946G4RI4XHD3"  # Alpha Vantage


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
    """Candles de 1 minuto do VIX via Alpha Vantage."""
    url = (
        "https://www.alphavantage.co/query?"
        "function=TIME_SERIES_INTRADAY&symbol=VIX&interval=1min&apikey=" + API_KEY
    )

    r = requests.get(url).json()

    if "Time Series (1min)" not in r:
        print("Erro ao obter histórico da Alpha Vantage:", r)
        return None

    ts = r["Time Series (1min)"]

    df = pd.DataFrame([
        {
            "timestamp": datetime.fromisoformat(t.replace(" ", "T")),
            "close": float(values["4. close"])
        }
        for t, values in ts.items()
    ])

    df = df.sort_values("timestamp")
    df = df.reset_index(drop=True)

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

    print("\n--- VARIAÇÕES ---")
    print(f"5 min:  {var_5:.2f}%")
    print(f"15 min: {var_15:.2f}%")
    print(f"30 min: {var_30:.2f}%")
    print(f"60 min: {var_60:.2f}%")

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

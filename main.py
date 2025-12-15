import time
from datetime import datetime
import pandas as pd

from tradingview_ta import TA_Handler, Interval
from tvDatafeed import TvDatafeed, Interval as TVInterval


def get_vix_price():
    """Retorna o preço atual do VIX (1 minuto)."""
    vix = TA_Handler(
        symbol="VIX",
        screener="america",
        exchange="TVC",
        interval=Interval.INTERVAL_1_MIN
    )
    data = vix.get_analysis()
    return data.indicators["close"]


def get_vix_history(n_bars=120):
    """Retorna histórico de n_bars candles de 1 minuto do VIX."""
    tv = TvDatafeed()  # login anônimo
    candles = tv.get_hist(
        symbol='VIX',
        exchange='TVC',
        interval=TVInterval.in_1_min,
        n_bars=n_bars
    )
    return candles


def variacao(atual, passado):
    """Calcula variação percentual entre dois preços."""
    return (atual - passado) / passado * 100


def process_vix():
    """Coleta dados do VIX, calcula variações e salva log."""
    print("\n--- COLETANDO DADOS DO VIX ---")
    agora = datetime.now().isoformat(timespec="seconds")
    print(f"Horário: {agora}")

    try:
        preco_atual = get_vix_price()
        print(f"Preço atual do VIX: {preco_atual}")
    except Exception as e:
        print("Erro ao pegar preço atual do VIX:", e)
        return

    try:
        dados = get_vix_history(n_bars=120)
    except Exception as e:
        print("Erro ao pegar histórico do VIX:", e)
        return

    if dados is None or len(dados) < 60:
        print("Histórico insuficiente para cálculos.")
        return

    # Garantir ordenação por tempo
    dados = dados.sort_index()

    try:
        preco_5 = dados.iloc[-5]["close"]
        preco_15 = dados.iloc[-15]["close"]
        preco_30 = dados.iloc[-30]["close"]
        preco_60 = dados.iloc[-60]["close"]
    except Exception as e:
        print("Erro ao acessar candles específicos:", e)
        return

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
    df.to_csv("vix_log.csv", mode="a", header=not pd.io.common.file_exists("vix_log.csv"), index=False)

    print("Registro salvo em vix_log.csv")


def main():
    """Loop infinito rodando a cada 60 segundos."""
    print("Iniciando monitor de VIX na Railway...")
    while True:
        process_vix()
        print("Aguardando 60 segundos para próxima coleta...\n")
        time.sleep(60)


if __name__ == "__main__":
    main()

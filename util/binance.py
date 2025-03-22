import ccxt
import pandas as pd

binance = ccxt.binance()
binance_futures = ccxt.binanceusdm()

MIN_24H_VOLUME = 500_000_000  # 5억 USDT

def get_price(symbol="BTC/USDT"):
    return binance.fetch_ticker(symbol)["last"]

def get_volume(symbol="BTC/USDT"):
    return binance.fetch_ticker(symbol)["quoteVolume"]

def get_ohlcv(symbol="BTC/USDT", timeframe="15m", limit=100):
    ohlcv = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    return df

def get_top_volume_symbols():
    tickers = binance_futures.fetch_tickers()
    symbols = []

    for symbol, data in tickers.items():
        if not symbol.endswith("USDT"):
            continue

        volume = data.get("quoteVolume")
        if volume and volume >= MIN_24H_VOLUME:
            symbols.append(symbol)

    return symbols
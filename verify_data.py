#!/usr/local/bin/python3.6
#coding = UTF-8
from functions import get_para_profit
import time


symbols = ["EOS/USDT", "ETH/USDT", "BTC/USDT", "EOS/BTC", 'ETH/BTC']
for symbol in symbols:
    symbol = symbol.lower().replace("/", "")
    path = 'profit/%s/%s_%s_profit.xlsx' % (symbol, symbol, time.strftime("%Y-%m-%d"))
    df = get_para_profit(path=path, kline=100, times=3, leverage_rate=2)
    print(df.sort_values(by="equity_curve", ascending=False))

import ccxt
import pandas as pd
from function.Functions import transfer_to_period_data



#初始化参数
time_interval = "1m"
count = 1000


# 设置翻墙代理
exchange = ccxt.bitfinex({
    'proxies': {
        'http': 'http://127.0.0.1:1087',
        'https': 'http://127.0.0.1:1087',
    },
})

exchange.apiKey = "uSuQ8FMuuk1BJgQAmyQVbLtIHm4wGn0nuIL00cvIjW8"
exchange.secret = "0myTvqw9Hu8amQ4TgqZdv4HEVthohQAM0558qpi3olR"


# balance = exchange.fetch_balance()
# for k, v in balance.items():
#     print(k, v)

# trade = exchange.fetch_trades("EOS/USDT")
# for item in trade:
#     print(item["info"]["price"])


# content = exchange.fetch_ohlcv(symbol, since=0, timeframe=time_interval, limit=count)

#下margin单
# params = {"type": "market"}
# result = exchange.create_order(symbol="EOS/USDT", type="limit", side="buy", amount=2, price="0.1", params=params)
# print(result)

#获取margin余额
margin_balance = exchange.fetch_balance({"type": "trading"})
# for k, v in margin_balance.items():
#     print(k, v)
# print(margin_balance)
symbol = "EOS/USDT"


price = exchange.fetch_ticker(symbol)['bid']



amount = 2
price = 1.1
# order_info = exchange.create_limit_buy_order(symbol, amount, price)
# order_info = exchange.fetch_my_trades(symbol=symbol)
# for item in order_info:
#     print(item)


# margin_info = exchange.create_order(symbol=symbol, type="limit",side='buy',amount=2,price=2.2, params={'type':'margin'})
trade_amount = 1
margin_info = exchange.create_order(symbol,"limit","sell",1,2.2,{'type': 'createmarginBuyOrder'})
print(margin_info)
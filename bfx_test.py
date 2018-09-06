import ccxt
exchange = ccxt.bitfinex({
    'proxies': {
        'http': 'http://127.0.0.1:1087',
        'https': 'http://127.0.0.1:1087',
    },
})

exchange.apiKey = "uSuQ8FMuuk1BJgQAmyQVbLtIHm4wGn0nuIL00cvIjW8"
exchange.secret = "0myTvqw9Hu8amQ4TgqZdv4HEVthohQAM0558qpi3olR"

symbol = "EOS/USDT"
'''
#获取margin余额
margin_balance = exchange.fetch_balance({'type': 'trading'})
#获取margin账号的具体币余额
print(margin_balance["EOS"])
#返回信息 {'free': 0.0, 'used': 10.96992216, 'total': 10.96992216}



#下 margin limit 多单

params = { 'type': 'limit', "price": "5.8"}
#params参数决定订单类型，是限价还是市场，下单价格为params中的价格，并非create_order 的价格
result = exchange.create_order(symbol=symbol, type="limit", side="buy", price=1.1, amount=15, params=params)

#下margin market 空单，market单
params = { 'type': 'market'}
#params参数决定订单类型，是限价还是市场，下单价格为params中的价格，并非create_order 的价格
result = exchange.create_order(symbol=symbol, type="limit", side='sell', amount=2, params=params)

# 下margin market 空单，限价单
params = {'type': 'limit', "price":"8"}
result = exchange.create_market_sell_order(symbol=symbol, amount=2, params=params)
'''
#获取先有margin的仓位
margin_pos = exchange.private_post_positions()
params = {'type': 'market'}
# order_info = exchange.create_market_sell_order(symbol=symbol, amount=2, params=params)
print(margin_pos)
# print(order_info)

# 下margin market单
# params = {'type': 'limit', "price":"8"}
# result = exchange.create_market_sell_order(symbol=symbol, amount=2, params=params)
# print(result)


#获取订单信息
# ord_info = exchange.fetch_order(id=16318505236)
# print(ord_info)
# print(ord_info['info']['price'])        #价格
# print(ord_info['info']['type'])         #类型，limit or market

#取消
# can_info = exchange.cancel_order(id=16318789828)
# print(can_info)





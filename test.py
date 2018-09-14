
import ccxt
import pandas as pd
import time, datetime
from function.Signals import signal_bolling
from function.Trade import next_run_time
from function.Trade import get_bitfinex_candle_data
from function.Trade import auto_send_email
'''
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 2000)

"""
自动交易主要流程

# 通过while语句，不断的循环

# 每次循环中需要做的操作步骤
    1. 更新账户信息
    2. 获取实时数据
    3. 根据最新数据计算买卖信号 
    4. 根据目前仓位、买卖信息，结束本次循环，或者进行交易
    5. 交易
"""

# =====参数
time_interval = '15m'  # 间隔运行时间，不能低于5min
count = 1000
leverage_rate = 2.8
# 设置翻墙代理
exchange = ccxt.bitfinex({
    'proxies': {
        'http': 'http://127.0.0.1:1087',
        'https': 'http://127.0.0.1:1087',
    },
})

exchange.apiKey = "uSuQ8FMuuk1BJgQAmyQVbLtIHm4wGn0nuIL00cvIjW8"
exchange.secret = "0myTvqw9Hu8amQ4TgqZdv4HEVthohQAM0558qpi3olR"

symbol = "ETH/USDT"
base_coin = symbol.split('/')[-1]
trade_coin = symbol.split('/')[0]

para = [100, 3]  # 策略参数

n = 0
print("ddd", exchange.fetch_balance())
# =====主程序
while True:
    # ===监控邮件内容
    email_title = '策略报表'
    email_content = ''
    n += 1
    #定义margin交易参数
    params = {'type': 'market'}
    print("======= 第%s次交易开始，交易开始时间为%s =======" % (n, datetime.datetime.now()))
    time.sleep(10)
    # ===从服务器更新账户balance信息, {'type': 'trading'} 为margin账号
    try:
        balance = exchange.fetch_balance({'type': 'trading'})['total']
        base_coin_amount = float(balance[base_coin])
        trade_coin_amount = float(balance[trade_coin])
        #定义下单(包含多单，空单)的数量，通过杠杆下单，
        order_margin_amount = trade_coin_amount * leverage_rate
    except Exception as e:
        print("获取余额异常：", e)
        continue

    print("test!!!!!!!", order_margin_amount)
'''




username = input("username:")
password = input("password:")

print(username, password)

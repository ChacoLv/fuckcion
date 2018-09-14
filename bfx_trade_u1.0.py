#!/usr/local/bin/python3.6
#coding = UTF-8
import ccxt
import pandas as pd
import time, datetime
from function.Signals import signal_bolling
from function.Trade import next_run_time
from function.Trade import get_bitfinex_candle_data
from function.Trade import auto_send_email
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
para = [100, 3]  # 策略参数
n = 0
mini_ord_account = 0.04

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

# =====主程序
while True:
    # ===监控邮件内容
    email_title = '策略报表'
    email_content = ''
    n += 1
    #定义margin交易参数
    params = {'type': 'market'}
    print("======= 第%s次交易开始，交易开始时间为%s =======" % (n, datetime.datetime.now()))

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

    print('margin account:', base_coin, base_coin_amount, trade_coin, trade_coin_amount)
    print('order_margin_amount:', order_margin_amount)
    # ===sleep直到运行时间
    run_time = next_run_time(time_interval)
    time.sleep(max(0, (run_time - datetime.datetime.now()).seconds))
    while True:  # 在靠近目标时间时
        if datetime.datetime.now() < run_time:
            continue
        else:
            break
    # ===获取最新数据
    while True:
        # 获取数据
        try:
            df = get_bitfinex_candle_data(exchange, symbol, time_interval, limit=count)                             #此部分需要加入异常处理（网络异常），加日志
            # 判断是否包含最新的数据
            _temp = df[df['candle_begin_time'] == (run_time - datetime.timedelta(minutes=int(time_interval.strip('m'))))]
            if _temp.empty:
                print('获取数据不包含最新的数据，重新获取')
                continue
            else:
                break
        except Exception as e:
            print("连接bfx异常", e)
            continue

    df = df[df['candle_begin_time'] < pd.to_datetime(run_time)]  # 去除target_time周期的数据
    df = signal_bolling(df, para=para)
    signal = df.iloc[-1]['signal']
    print(df.iloc[800:])
    print('\n交易信号', signal)
    while str(signal) != "nan":
        try:
            # 获取现有账号margin 仓位
            margin_pos = exchange.private_post_positions()
            print("margin info:", margin_pos)
            if len(margin_pos) != 0 and signal == 0:
                print('\n卖出')
                #如果是做多单的话，则需要通过sell 来卖掉这些多单
                margin_pos_amount = float(exchange.private_post_positions()[0]['amount'])
                margin_profit = float(exchange.private_post_positions()[0]["pl"])
                if margin_pos_amount >0:
                    # 清空现有仓位,下市价单
                    order_info = exchange.create_market_sell_order(symbol=symbol, amount=margin_pos_amount, params=params)
                    price = order_info['info']['price']

                #如果是做多单的话，则需要通过buy 来卖掉这些空单
                elif margin_pos_amount < 0:
                    order_info = exchange.create_market_buy_order(symbol=symbol, amount=-margin_pos_amount, params=params)
                    price = order_info['info']['price']

                # 邮件标题
                email_title += '_卖出_' + trade_coin
                # 邮件内容
                email_content += '卖出信息：\n'
                email_content += '卖出数量：' + str(margin_pos_amount) + '\n'
                email_content += '卖出价格：' + str(price) + '\n'
                email_content += '卖出获利：' + str(margin_profit) + '\n'
            # 买入多单
            if len(margin_pos) == 0 and signal == 1:
                print('\n买入')
                # 买入多单
                order_info = exchange.create_market_buy_order(symbol=symbol, amount=order_margin_amount, params=params)
                price = order_info['info']['price']
                # 邮件标题
                email_title += '_买入多单_' + trade_coin
                # 邮件内容
                email_content += '买入信息：\n'
                email_content += '买入数量：' + str(order_margin_amount) + '\n'
                email_content += '买入价格：' + str(price) + '\n'
            # 买入空单
            if len(margin_pos) == 0 and signal == -1:
                print('\n买入')
                # 买入多单
                order_info = exchange.create_market_sell_order(symbol=symbol, amount=order_margin_amount, params=params)
                price = order_info['info']['price']
                # 邮件标题
                email_title += '_买入空单_' + trade_coin
                # 邮件内容
                email_content += '买入信息：\n'
                email_content += '买入数量：' + str(order_margin_amount) + '\n'
                email_content += '买入价格：' + str(price) + '\n'
            break
        except Exception as e:
            print("交易异常：", e)
            continue

    # =====发送邮件
    # 每个半小时发送邮件
    if run_time.minute % 30 == 0:
        # 发送邮件
        auto_send_email('clv89@mail.yst.com.cn', email_title, email_content)
    # =====本次交易结束
    print(email_title)
    print(email_content)
    print('=====本次运行完毕\n\n\n')
    time.sleep(6 * 1)

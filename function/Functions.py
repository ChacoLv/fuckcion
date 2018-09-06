import pandas as pd
import numpy as np
import ccxt, time , os
import calendar, datetime
from function.Signals import signal_bolling
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 1000)


#日期加一个月
def add_month(date):
    # number of days this month
    month_days = calendar.monthrange(date.year, date.month)[1]
    candidate = date + datetime.timedelta(days=month_days)
    # but maybe we are a month too far
    if candidate.day != date.day:
        # go to last day of next month,
        # by getting one day before begin of candidate month
        return candidate.replace(day=1) - datetime.timedelta(days=1)
    else:
        return candidate

#K线转化
def transfer_to_period_data(df, rule_type='15T'):
    """
    将数据转换为其他周期的数据
    :param df:
    :param rule_type:
    :return:
    """

    # =====转换为其他分钟数据
    period_df = df.resample(rule=rule_type, on='candle_begin_time', label='left', closed='left').agg(
        {'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'volume': 'sum',
         })
    period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
    period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
    period_df.reset_index(inplace=True)
    df = period_df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]

    return df

#从bitfinex获取历史数据，并保存成hdf文件格式
def get_hist_candle_bitfinex(symbol, time_interval, count):
    """
    从bitfinex抓取kline的历史数据
    :param symbol: 交易对
    :param time_interval: 获取的时间间隔
    :param count: 一次获取的candle数量
    :return:
    """
    # 设置翻墙代理
    exchange = ccxt.bitfinex()
    # exchange = ccxt.bitfinex({
    #     'proxies': {
    #         'http': 'http://127.0.0.1:1087',
    #         'https': 'http://127.0.0.1:1087',
    #     },
    # })
    #参数初始化
    # n = 0
    since_time = 0                  #bitfinex since_time=0会从交易对上交易所时间开始计算
    now_time = int(time.time())    #获取当前时间
    all_data = pd.DataFrame()
    while since_time <= now_time * 1000:        #当从bitfinex拉取数据的时候，开始时间大于现在时间的时候，则停止
    # while n <= 2:
        try:
            content = exchange.fetch_ohlcv(symbol, since=since_time, timeframe=time_interval, limit=count)
            since_time = content[-1][0] + 60000     #从获取的最后一个时间加1min作为下次开始的时间

            # 整理数据
            df = pd.DataFrame(content, dtype=float)
            df.rename(columns={0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}, inplace=True)
            df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')
            df['candle_begin_time'] = df['candle_begin_time'] + datetime.timedelta(hours=8)
            df = df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]
            all_data = all_data.append(df)
            time.sleep(10)                   #bitfinex对rest api调用有限制，过于频繁会报ddos错误
        except Exception as e:
            print("出现异常:", e)
            all_data.index = range(len(all_data))  # 重置index
            if "time out：" in str(e):
                print("time out：", e)
                time.sleep(5)
            else:
                print("出现异常", e)
                continue
        # n = n + 1
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(since_time/1000)))
    all_data.index = range(len(all_data))       #重置index
    all_data.to_hdf("data/%s_%s_%s_data.h5" % (symbol.replace("/", '').lower(), "0808", time_interval), key='all_data', mode="w")

#计算单个交易对历史获利情况
def equity_curve_with_long_and_short(df, leverage_rate, c_rate=2.0/1000, min_margin_rate=0.15):
    """

    :param df:  带有signal和pos的原始数据
    :param leverage_rate:  bfx交易所最多提供3倍杠杆，leverage_rate可以在(0, 3]区间选择
    :param c_rate:  手续费
    :param min_margin_rate:  低保证金比例，必须占到借来资产的15%
    :return:
    """

    # =====基本参数
    init_cash = 100  # 初始资金
    min_margin = init_cash * leverage_rate * min_margin_rate  # 最低保证金

    # =====根据pos计算资金曲线
    # ===计算涨跌幅
    df['change'] = df['close'].pct_change(1)  # 根据收盘价计算涨跌幅
    df['buy_at_open_change'] = df['close'] / df['open'] - 1  # 从今天开盘买入，到今天收盘的涨跌幅
    df['sell_next_open_change'] = df['open'].shift(-1) / df['close'] - 1  # 从今天收盘到明天开盘的涨跌幅
    df.at[len(df) - 1, 'sell_next_open_change'] = 0

    # ===选取开仓、平仓条件
    condition1 = df['pos'] != 0
    condition2 = df['pos'] != df['pos'].shift(1)
    open_pos_condition = condition1 & condition2

    condition1 = df['pos'] != 0
    condition2 = df['pos'] != df['pos'].shift(-1)
    close_pos_condition = condition1 & condition2

    # ===对每次交易进行分组
    df.loc[open_pos_condition, 'start_time'] = df['candle_begin_time']
    df['start_time'].fillna(method='ffill', inplace=True)
    df.loc[df['pos'] == 0, 'start_time'] = pd.NaT

    # ===计算仓位变动
    # 开仓时仓位
    df.loc[open_pos_condition, 'position'] = init_cash * leverage_rate * (1 + df['buy_at_open_change'])  # 建仓后的仓位

    # 开仓后每天的仓位的变动
    group_num = len(df.groupby('start_time'))
    if group_num > 1:
        t = df.groupby('start_time').apply(lambda x: x['close'] / x.iloc[0]['close'] * x.iloc[0]['position'])
        t = t.reset_index(level=[0])
        df['position'] = t['close']
    elif group_num == 1:
        t = df.groupby('start_time')[['close', 'position']].apply(lambda x: x['close'] / x.iloc[0]['close'] * x.iloc[0]['position'])
        df['position'] = t.T.iloc[:, 0]

    # 每根K线仓位的最大值和最小值，针对最高价和最低价
    df['position_max'] = df['position'] * df['high'] / df['close']
    df['position_min'] = df['position'] * df['low'] / df['close']

    # 平仓时仓位
    df.loc[close_pos_condition, 'position'] *= (1 + df.loc[close_pos_condition, 'sell_next_open_change'])

    # ===计算每天实际持有资金的变化
    # 计算持仓利润
    df['profit'] = (df['position'] - init_cash * leverage_rate) * df['pos']  # 持仓盈利或者损失

    # 计算持仓利润最小值
    df.loc[df['pos'] == 1, 'profit_min'] = (df['position_min'] - init_cash * leverage_rate) * df['pos']  # 最小持仓盈利或者损失
    df.loc[df['pos'] == -1, 'profit_min'] = (df['position_max'] - init_cash * leverage_rate) * df['pos']  # 最小持仓盈利或者损失

    # 计算实际资金量
    df['cash'] = init_cash + df['profit']  # 实际资金
    df['cash'] -= init_cash * leverage_rate * c_rate  # 减去建仓时的手续费
    df['cash_min'] = df['cash'] - (df['profit'] - df['profit_min'])  # 实际最小资金
    df.loc[close_pos_condition, 'cash'] -= df.loc[close_pos_condition, 'position'] * c_rate  # 减去平仓时的手续费

    # ===判断是否会爆仓
    out_of_stock = 0
    _index = df[df['cash_min'] <= min_margin].index
    if len(_index) > 0:
        print('有爆仓')
        out_of_stock = 1
        df.loc[_index, '强平'] = 1
        df['强平'] = df.groupby('start_time')['强平'].fillna(method='ffill')
        df.loc[(df['强平'] == 1) & (df['强平'].shift(1) != 1), 'cash_强平'] = df['cash_min']  # 此处是有问题的
        df.loc[(df['pos'] != 0) & (df['强平'] == 1), 'cash'] = None
        df['cash'].fillna(value=df['cash_强平'], inplace=True)
        df['cash'] = df.groupby('start_time')['cash'].fillna(method='ffill')
        df.drop(['强平', 'cash_强平'], axis=1, inplace=True)  # 删除不必要的数据

    # ===计算资金曲线
    df['equity_change'] = df['cash'].pct_change()
    df.loc[open_pos_condition, 'equity_change'] = df.loc[open_pos_condition, 'cash'] / init_cash - 1  # 开仓日的收益率
    df['equity_change'].fillna(value=0, inplace=True)
    df['equity_curve'] = (1 + df['equity_change']).cumprod()

    # ===删除不必要的数据
    df.drop(['change', 'buy_at_open_change', 'sell_next_open_change', 'start_time', 'position', 'position_max',
             'position_min', 'profit', 'profit_min', 'cash', 'cash_min'], axis=1, inplace=True)

    return df, out_of_stock

#验证单个交易对在不同参数情况下对获利情况
def verify_hist_data_profit(df, begin_time, end_time, rule_type="15T"):
    """
    :param df: 为1min的历史数据信息
    :param begin_time: 计算获利的开始时间
    :param end_time: 计算获利的结束时间
    :param rule_type: 改变成什么类型的K线
    :return:
    """
    # 转换数据周期
    df = transfer_to_period_data(df, rule_type)
    # 选取时间段
    df = df[df['candle_begin_time'] >= pd.to_datetime(begin_time)]
    df = df[df['candle_begin_time'] <= pd.to_datetime(end_time)]
    df.reset_index(inplace=True, drop=True)

    # 构建参数候选组合
    n_list = range(100, 101, 25)  # 过去多少个K线为一组均线
    m_list = [2]  # boll线是均线的几倍数
    leverage_list = [3]
    cash = 100
    rtn = pd.DataFrame(
        columns=['Kline_num', 'boll_times', 'init_cash', 'leverage_rate', 'equity_curve', 'out_of_stock'])
    # 遍历所有参数组合
    for m in m_list:
        for n in n_list:
            para = [n, m]
            for leverage_rate in leverage_list:
                # 计算交易信号
                df = signal_bolling(df.copy(), para)
                # 计算资金曲线
                df, out_of_stock = equity_curve_with_long_and_short(df=df, leverage_rate=leverage_rate,
                                                                    c_rate=2.0 / 1000)
                rtn_list = [para[0], para[1], cash, leverage_rate, df.iloc[-1]['equity_curve'],
                            out_of_stock]               # 获取相应的值，转化为list
                rtn.set_value(len(rtn), list(rtn.columns), np.array(rtn_list))  #保存数据
                print("K线数:%s,倍数:%s 初始资金:%s, 杠杆率:%s,是否爆仓:%s"
                      % (para[0], para[1], cash, leverage_rate, out_of_stock),
                      '策略最终收益：', df.iloc[-1]['equity_curve'])

    return rtn

#将获利数据保存，可以选取期间来观察获利信息
def save_hist_verify_data_to_excel(df, begin_time, end_time, path):
    """
    根据一个交易对的历史获利情况，计算从开始时间至结束时间中，每增加一个月的获利情况计算
    将不通开始时间至结束时间的获利结果保存成一个sheet,整体保存成excel

    :param df: 一个交易对历史的获利情况
    :param begin_time: 计算获利的开始时间
    :param end_time: 计算获利的结束时间
    :param path: 保存excel的路径
    """

    #设置excel文件
    writer = pd.ExcelWriter(path=path)

    #测试某一时间段的利润效果
    while begin_time < end_time:
        str_begin = str(begin_time.year) + '-' + str(begin_time.month)           #设置excel中sheet名称
        str_end = str(end_time.year) + '-' + str(end_time.month)
        try:

            profit_result = verify_hist_data_profit(df=df, begin_time=begin_time, end_time=end_time)       #保存每个时间段排序好的对比数据至excel中的sheet上
            profit_result = profit_result.sort_values(by="equity_curve", ascending=False)
            profit_result.to_excel(writer, "%s_%s" % (str_begin, str_end))
            writer.save()
        except Exception as e:
            print("save to excel error:", e)
        begin_time = add_month(begin_time)

#获取一个excel中不同sheet中， 相同参数不同的时间段的获利情况
def get_para_profit(path, kline, times, leverage_rate):
    """
    根据不通交易对不通时间段的历史获利情况进行计算不同参数的获利情况

    :param path: 为一个不同时间段的获利情况的excel路径，是对excel内的数据进行分析
    :param kline: boll历史开线数量
    :param times: boll倍数
    :param leverage_rate: 杠杆倍率
    """
    xls = pd.ExcelFile(path)
    xls_sheets = xls.sheet_names
    rtn = pd.DataFrame(columns=["section", "equity_curve", "out_of_stock"])
    for sheet_name in xls_sheets:
        df = pd.read_excel(path, sheet_name=sheet_name)
        df.reset_index(inplace=True, drop=True)
        df = df[(df.Kline_num == kline) & (df.boll_times == times) & (df.leverage_rate ==leverage_rate)]
        np_list = [sheet_name, df.iloc[-1]["equity_curve"], df.iloc[-1]['out_of_stock']]
        rtn.set_value(len(rtn), list(rtn.columns), np.array(np_list))
    rtn['equity_curve'] = rtn[["equity_curve"]].astype(float)      #将获利情况设置成fload类型，以便进行排序
    rtn = rtn.sort_values(by="equity_curve", ascending=False)
    rtn.reset_index(inplace=True, drop=True)
    return rtn


















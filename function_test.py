from function.Functions import verify_hist_data_profit
from function.Functions import save_hist_verify_data_to_excel
from function.Signals import signal_bolling
from function.Functions import get_para_profit
import pandas as pd
import datetime
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)

'''

#测试历史获利情况
df = pd.read_hdf("data/ethusdt_2018-08-25_1m_data.h5", key="all_data")
# print(df)

begin_time = datetime.datetime.strptime("2017-1-1", "%Y-%m-%d")
end_time = datetime.datetime.strptime("2018-8-25", "%Y-%m-%d")

rtn = verify_hist_data_profit(df=df, begin_time=begin_time, end_time=end_time)
print(rtn)
'''



#测试参数对

path = "profit/ethusdt/ethusdt_2018-08-25.xlsx"
kline = 100
times = 3
leverage_rate = 3
print(get_para_profit(path=path, kline=100, times=times, leverage_rate=leverage_rate))

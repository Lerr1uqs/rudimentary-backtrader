import backtrader as bt
import pandas as pd
import pdb
import datetime
from loguru import logger
from typing import List, Type
import quantstats as qs
from pandas import DataFrame
from ta.trend import MACD
from ta.momentum import StochasticOscillator
from loguru import logger
import numpy as np
import sys
pd.set_option('display.unicode.east_asian_width', True)

df = pd.read_csv("strategies/macd_kd/sinoma.5min.csv")
df = df.iloc[:1000].copy()

df["date"] = pd.to_datetime(df["date"])

macd = MACD(df["close"], window_fast=12, window_slow=26, window_sign=9)
df["macd_hist"] = macd.macd_diff()

# 添加 KDJ 指标
sto_result_series = [(np.NaN, np.NaN)] # List(k, d)

for i in range(1, len(df)):

    truncated_dataframe = df.iloc[0:i]
    truncated_dataframe.set_index("date", drop=True, inplace=True)
    truncated_dataframe.sort_index(ascending=True, inplace=True)

    resampled_df = truncated_dataframe.resample('15min').agg({
        'open'  : 'first',
        'high'  : 'max',
        'low'   : 'min',
        'close' : 'last',
        'volume': 'sum',
    }).dropna() # NOTE: 中间间隔时间不开盘

    sto = StochasticOscillator(
        high          = resampled_df['high'], 
        low           = resampled_df['low'],
        close         = resampled_df['close'],
        window        = 14, 
        smooth_window = 3, 
        fillna        = False # TODO:
    )
    # if i > 30:
    #     pdb.set_trace()
    sto_result_series.append((sto.stoch().iloc[-1], sto.stoch_signal().iloc[-1]))

df["k_15min"] = pd.Series([x[0] for x in sto_result_series])
df["d_15min"] = pd.Series([x[1] for x in sto_result_series])
logger.info("indicator generate done")

import backtrader.feeds as btfeeds

class ExtendPandasData(btfeeds.PandasData):


    lines = ('macd_hist',
             'k_15min',
             'd_15min')

    # add the parameter to the parameters inherited from the base class
    #  -1 : autodetect position or case-wise equal name
    #  string : column name (as index) in the pandas dataframe
    params = (('macd_hist', -1),
              ('k_15min', -1),
              ('d_15min', -1),)

class MacdBtIndicator(bt.Indicator):
    lines = ('macd_hist', "k_15min", "d_15min")
    params = (
        ("k_15min", None),
        ("j_15min", None),
    )

    def __init__(self):
        if self.p.k_15min is None or self.p.j_15min is None:
            raise ValueError("k_15min and j_15min must be specified")
        

# from bt.indcator 
# MACD: https://www.investopedia.com/terms/m/macd.asp#:~:text=Key%20Takeaways,from%20the%2012%2Dperiod%20EMA.
# KDJ : https://www.investopedia.com/terms/s/stochasticoscillator.asp
# KDJ : https://en.wikipedia.org/wiki/Stochastic_oscillator
class MACDKDJ(bt.Strategy):
    params = (
        # The MACD line is calculated by subtracting the 26-period exponential moving average (EMA) from the 12-period EMA.
        ('period_me1', 12), # fast
        ('period_me2', 26), # slow
        # The signal line is a nine-period EMA of the MACD line.
        ('period_signal', 9),

        ('kdj_period', 14),
        ('kdj_smoothK', 3),
        ('period_dslow', 3),
    )

    # lines = (
    #     'macd_hist', "k_15min", "d_15min"
    # )
    def __init__(self):
        # 添加 MACD 指标
        # import pdb; pdb.set_trace()
        # print(self.data.macd_hist)
        self.startup_candle_count = 36
        self.idx = 0
        self.cur_pos_status = None

        self.total_pnl = 0

        logger.remove()
        logger.add(sys.stdout, level="DEBUG")

    def next(self):

        if self.idx < self.startup_candle_count:
            self.idx += 1
            return
        
        # 买入条件
        # pdb.set_trace()
        if self.data_macd_hist[0] > self.data_macd_hist[-1] and \
            self.data_k_15min[0] > self.data_d_15min[0]:

            curtime = self.data.datetime.datetime(0)
            if self.position.size < 0: # is short
                logger.info(f"long  at {curtime} 20 * {self.data.close[-1]}")
                self.close()
                self.buy(size=10)
                # self.position.close()
            elif self.position.size > 0:
                pass
            else: # no position
                logger.info(f"long  at {curtime} 10 * {self.data.close[-1]}")
                self.buy(size=10)

            # if not self.position:
            # if self.last_status != "long":
            #     self.last_status = "long"
            #     self.buy(size=1)

        # 卖出条件
        if self.data_macd_hist[0] < self.data_macd_hist[-1] and \
            self.data_k_15min[0] < self.data_d_15min[0]:

            curtime = self.data.datetime.datetime(0)
            if self.position.size < 0:
                pass
            elif self.position.size > 0:
                logger.info(f"short at {curtime} 20 * {self.data.close[-1]}")
                self.close()
                self.sell(size=10)
            else: # no position
                logger.info(f"short at {curtime} 10 * {self.data.close[-1]}")
                self.sell(size=10)

    def notify_order(self, order: bt.Order):
        if order.Status[order.status] == "Completed":
            logger.debug(f"type:{order.OrdTypes[order.ordtype]}, size:{order.size}, price:{order.price}")
        return 

    def notify_trade(self, trade: bt.trade.Trade):
        if trade.isclosed:
            # 当交易平仓时，计算利润
            # pdb.set_trace()
            # profit = trade.profit
            # self.orders.append(profit)
            self.total_pnl += trade.pnlcomm 
            profit_rate = trade.pnlcomm / trade.price
            logger.info(f"Trade closed: pftrate = {profit_rate * 100:.2f}%")

    def stop(self):
        logger.info(f"Total PnL: {self.total_pnl:.3f}")

# df = df[selected_colomns]

cerebro = bt.Cerebro()
data = ExtendPandasData(
    dataname=df,
    datetime='date',  # 必须指定日期列的名称
    open='open',
    high='high',
    low='low',
    close='close',
    volume='volume',
    timeframe=bt.TimeFrame.Minutes,
    # fromdate=datetime.datetime(2021, 8, 16), 
    # todate=datetime.datetime(2022, 8, 15)
)# 以日频加载数据

logger.info("loading data...")
cerebro.adddata(data, name="SINOMA")
cerebro.addstrategy(MACDKDJ)
# Sizer: 它根据资产总价值的百分比来确定每次交易的大小 这里是每次交易90%
# cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="mysharp")
cerebro.addanalyzer(bt.analyzers.Returns, _name="myreturn")
cerebro.addanalyzer(bt.analyzers.PyFolio, _name="myfolio")
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据

# print(cerebro.broker.getvalue()) # NOTE: 默认10000.0$ 
cerebro.broker.setcash(1_0000)
origin_cash = cerebro.broker.getvalue()

results: List[bt.Strategy] = cerebro.run()
# logger.debug(result[0].analyzers.myreturn)

mysharp : bt.analyzers.SharpeRatio = results[0].analyzers.mysharp
myreturn: bt.analyzers.Returns     = results[0].analyzers.myreturn
pnl     : bt.analyzers.TimeReturn  = results[0].analyzers.pnl

# 夏普率的本质就是 收益率/波动率 波动率就是用标准差计算
# logger.info("夏普率: {:.2f}".format(mysharp.get_analysis()['sharperatio']))
# logger.info("总回报率: {:.2%}".format(myreturn.get_analysis()['rtot']))
logger.info("账户原始余额: {}".format(origin_cash))
logger.info("账户回测余额: {:.1f}".format(cerebro.broker.getvalue()))
# logger.info(f"收益率时序数据: {pnl.get_analysis()}")

import matplotlib.pyplot as plt
# 设置DISPLAY变量进行X11本地绘图转发
cerebro.plot()
# plt.savefig('backtrader_plot.png')

pyfoliozer = results[0].analyzers.getbyname("myfolio")
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()


# from http.server import SimpleHTTPRequestHandler
# from socketserver import TCPServer

# # 定义端口号
# port = 8000

# # 创建HTTP服务器，并指定启动页为report.html
# handler = SimpleHTTPRequestHandler
# handler.extensions_map.update({
#     '.html': 'text/html',
#     '.js': 'application/javascript',
# })

# # 启动HTTP服务器
# httpd = TCPServer(('localhost', port), handler)
# print(f"Server started at http://localhost:{port}/report.html")
# print("Press Ctrl+C to stop the server.")

# try:
#     httpd.serve_forever()
# except KeyboardInterrupt:
#     print("\nServer stopped.")
#     httpd.server_close()
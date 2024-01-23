import backtrader as bt
import pandas as pd
import pdb
import datetime
from loguru import logger

# PARAMS = dict(period5=5, period30=30)# TODO: 回测参数

class DemoStrategy(bt.Strategy):
    
    def __init__(self) -> None:
        # 短均线和长均线交叉
        self.sma5  = bt.indicators.sma.MovingAverageSimple(
            self.data0.close, period=5
        )
        self.sma30 = bt.indicators.sma.MovingAverageSimple(
            self.data0.close, period=30
        )
        self.cross = bt.indicators.crossover.CrossOver(
            self.sma5, self.sma30
        )

    
    def next(self):
        # 编写交易策略
        if not self.position: # 是否有持仓
            if self.cross > 0: # 1.0 if the 1st data crosses the 2nd data upwards 这里代表着5日均线crossover30日均线向上
                self.buy()
        else:
            if self.cross < 0:
                self.sell()

    def log(self):
        pass

    def notify_order(self, order):
        pass

    def notify_trade(self, trade): # TODO:
        logger.debug(type(trade))
        if trade.isclosed:
            logger.info(
                "Trade Profit, Cross {}, next {}".format(
                    trade.pnl, trade.pnlcomm
                )
            )

    

df = pd.read_csv("assets/yiling.csv")
# not use the "Adj Close" colomn
selected_colomns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
df.loc[:, 'Date'] = pd.to_datetime(df['Date'])
# df = df[selected_colomns]

cerebro = bt.Cerebro()
data = bt.feeds.PandasData(
    dataname=df[selected_colomns],
    datetime='Date',  # TODO: 指定日期列的名称
    open='Open',
    high='High',
    low='Low',
    close='Close',
    volume='Volume',
    timeframe=bt.TimeFrame.Days,
    fromdate=datetime.datetime(2021, 8, 16), # TODO: 去掉如何？
    todate=datetime.datetime(2022, 8, 15)
)# 以日频加载数据

cerebro.adddata(data, name="stockname")
cerebro.addstrategy(DemoStrategy)
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)# TODO:

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="mysharp") # TODO:
cerebro.addanalyzer(bt.analyzers.Returns, _name="myreturn") # TODO:

result = cerebro.run()
logger.info("夏普率: %f" % result[0].analyzers.mysharp.get_analysis()['sharperatio'])
logger.info("总回报率: %f" % result[0].analyzers.myreturn.get_analysis()['rtot'])

import matplotlib.pyplot as plt

cerebro.plot(style='candle', barup='green', bardown='red', iplot=False, volume=False, fmt_x_data='%Y-%m-%d %H:%M:%S')
plt.savefig('backtrader_plot.png')


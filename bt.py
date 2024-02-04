import backtrader as bt
import pandas as pd
import pdb
import datetime
from loguru import logger
from typing import List, Type
import quantstats as qs

# PARAMS = dict(period5=5, period30=30)# TODO: 回测参数

class DemoStrategy(bt.Strategy):
    
    def __init__(self) -> None:
        '''
        利用indicator绘制一些指标曲线
        '''
        # 短均线和长均线交叉
        self.sma5  = bt.indicators.MovingAverageSimple(
            self.data0.close, period=5
        )
        # self.sma30 = bt.indicators.MovingAverageSimple(
        #     self.data0.close, period=30
        # )
        # 事实证明 EMA效果更好
        self.ema20 = bt.indicators.ExponentialMovingAverage(
            self.data0.close, period=20
        )
        self.cross = bt.indicators.CrossOver(
            self.sma5, self.ema20
        )

    
    def next(self):
        '''
        实际的交易函数, 要等所有均线出现后才开始调用next, 否则是prenext
        '''
        if not self.position: # 是否有持仓
            if self.cross > 0: # 1.0 if the 1st data crosses the 2nd data upwards 这里代表着5日均线crossover30日均线向上
                self.buy()
        else:
            if self.cross < 0:
                self.sell()

    def log(self):
        pass

    def notify_order(self, order: bt.Order):
        '''
        订单状态变化的事件触发函数
        '''
        # Submitted -> Accepted -> Completed 这里应该是模拟了券商
        # logger.debug(f"notify_order {bt.OrderBase.Status[order.status]}")
        pass

    def notify_trade(self, trade: bt.Trade):
        '''
        交易状态变化的事件触发函数
        '''
        # pnl (Profit and Loss)
        # pnlcomm (Profit and Loss including Commissions)
        if trade.isclosed:
            logger.info(
                "Trade Profit : {:.2f}".format(trade.pnl)# 相比于买入的时候是亏损还是赚钱
            )


df = pd.read_csv("assets/yiling.csv")
# not use the "Adj Close" colomn
selected_colomns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
df.loc[:, 'Date'] = pd.to_datetime(df['Date'])
# df = df[selected_colomns]

cerebro = bt.Cerebro()
data = bt.feeds.PandasData(
    dataname=df[selected_colomns],
    datetime='Date',  # 必须指定日期列的名称
    open='Open',
    high='High',
    low='Low',
    close='Close',
    volume='Volume',
    timeframe=bt.TimeFrame.Days,
    # fromdate=datetime.datetime(2021, 8, 16), 
    # todate=datetime.datetime(2022, 8, 15)
)# 以日频加载数据

cerebro.adddata(data, name="yiling")
cerebro.addstrategy(DemoStrategy)
# Sizer: 它根据资产总价值的百分比来确定每次交易的大小 这里是每次交易90%
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="mysharp")
cerebro.addanalyzer(bt.analyzers.Returns, _name="myreturn")
cerebro.addanalyzer(bt.analyzers.PyFolio, _name="myfolio")

# print(cerebro.broker.getvalue()) # NOTE: 默认10000.0$ 
origin_cash = cerebro.broker.getvalue()

results: List[bt.Strategy] = cerebro.run()
# logger.debug(result[0].analyzers.myreturn)

mysharp : bt.analyzers.SharpeRatio = results[0].analyzers.mysharp
myreturn: bt.analyzers.Returns     = results[0].analyzers.myreturn

# 夏普率的本质就是 收益率/波动率 波动率就是用标准差计算
logger.info("夏普率: {:.2f}".format(mysharp.get_analysis()['sharperatio']))
logger.info("总回报率: {:.2%}".format(myreturn.get_analysis()['rtot']))
logger.info("账户原始余额: {}".format(origin_cash))
logger.info("账户回测余额: {:.1f}".format(cerebro.broker.getvalue()))

import matplotlib.pyplot as plt
# 设置DISPLAY变量进行X11本地绘图转发
cerebro.plot(style='candle', barup='green', bardown='red', iplot=False, volume=False, fmt_x_data='%Y-%m-%d %H:%M:%S')
plt.savefig('backtrader_plot.png')

pyfoliozer = results[0].analyzers.getbyname("myfolio")
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
# import pdb; pdb.set_trace()
# 这里的returns应该是相对于前一天的变化率 只有0.0x
qs.reports.html(returns, output="report.html") 

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# 定义端口号
port = 8000

# 创建HTTP服务器，并指定启动页为report.html
handler = SimpleHTTPRequestHandler
handler.extensions_map.update({
    '.html': 'text/html',
    '.js': 'application/javascript',
})

# 启动HTTP服务器
httpd = TCPServer(('localhost', port), handler)
print(f"Server started at http://localhost:{port}/report.html")
print("Press Ctrl+C to stop the server.")

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    httpd.server_close()

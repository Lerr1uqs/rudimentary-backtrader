import efinance as ef
import pandas as pd
pd.set_option('display.unicode.east_asian_width', True)
code = '600970'
df = ef.stock.get_quote_history(code, beg="20240101", end="20241120", klt=5)
print(df)
df.rename(columns={
    '股票名称': 'name',
    '股票代码': 'code',
    '日期':'date',
    '开盘':'open',
    '最高':'high',
    '最低':'low',
    '收盘':'close',
    '成交量':'volume',
},inplace=True)
df = df[['name', 'code', 'date', 'open', 'high', 'low', 'close', 'volume']]
print(df)
df.to_csv("sinoma.5min.csv")
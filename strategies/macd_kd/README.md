策略
美国期货: ESZ4(ES：标普500指数期货，Z：12月，4：2024年份)。
```
longCondition   = hist_5m>hist_5m[1] and k_15m>d_15m

shortCondition  = hist_5m<hist_5m[1] and k_15m<d_15m

if  longCondition
    持多仓1手

else if  shortCondition
    持空仓1手
```
难点在于多周期和未成形的K
另外就是收盘的优化

结果: 这种肯定不行
```shell
2024-11-23 00:57:22.190 | INFO     | __main__:notify_trade:174 - Trade closed: pftrate = 10.05%
2024-11-23 00:57:22.190 | INFO     | __main__:stop:177 - Total PnL: -9.800
2024-11-23 00:57:22.191 | INFO     | __main__:<module>:220 - 账户原始余额: 10000
2024-11-23 00:57:22.200 | INFO     | __main__:<module>:221 - 账户回测余额: 9990.4
```



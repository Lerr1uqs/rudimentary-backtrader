import numpy as np

# 十个月的每月收益率数据
monthly_returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.01, 0.03, -0.02, 0.01])

# 年化无风险利率
annual_rf_rate = 0.01

# 计算年化收益率（Rp）
annual_returns = np.prod(1 + monthly_returns) ** (12 / len(monthly_returns)) - 1

# 计算年化标准差（σp）
annual_std_dev = np.std(monthly_returns) * np.sqrt(12)

# 计算夏普率
sharpe_ratio = (annual_returns - annual_rf_rate) / annual_std_dev

print("年化收益率 Rp:", annual_returns)
print("年化标准差 σp:", annual_std_dev)
print("夏普率 Sharpe Ratio:", sharpe_ratio)
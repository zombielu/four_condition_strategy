from backtesting.test import GOOG
import pandas as pd

# 1. 看一下原始数据
print(GOOG.head())

# GOOG 是一个 DataFrame，index 是时间序列（日期），包含 Open, High, Low, Close, Volume

# 2. 定义一个简单指标函数，比如 5 日均线
def SMA(prices, n=5):
    return prices.rolling(n).mean()

# 3. 计算指标
GOOG['SMA5'] = SMA(GOOG['Close'], 5)

# 4. 查看前 10 行
print(GOOG.head(10))
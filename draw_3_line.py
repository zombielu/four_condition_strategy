from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import pandas as pd

class EMAStrategy(Strategy):
    short_period = 9
    mid_period = 13
    long_period = 21

    def init(self):
        # 封装 EMA 函数
        def ema(series, period):
            return pd.Series(series).ewm(span=period, adjust=False).mean()

        # 注册三个 EMA 指标
        self.ema_short = self.I(ema, self.data.Close, self.short_period)
        # self.ema_mid = self.I(ema, self.data.Close, self.mid_period)
        # self.ema_long = self.I(ema, self.data.Close, self.long_period)
        # self.ema_data = self.I(lambda s: s, self.data['Moving Average 1'], name = "ema_data")

    def next(self):
        # 简单策略示例
        # if self.ema_short[-1] > self.ema_long[-1] and not self.position:
        #     self.buy()
        # elif self.ema_short[-1] < self.ema_long[-1] and self.position:
        #     self.position.close()
        pass

# print(stats)
df = pd.read_csv('/Users/weilinwu/Documents/OANDA_XAUUSD, 15_c1cf9.csv')
df = df.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close'
})
df = df.iloc[-2000:]
bt = Backtest(df, EMAStrategy, cash=10_000, commission=0.001)
# stats = bt.run()
stats = bt.optimize(
    short_period=range(7, 11, 2),
    mid_period = range(11, 15, 2),
    long_period = range(19, 23, 2),
    maximize='Sharpe Ratio',
    constraint=lambda p: p.short_period < p.mid_period < p.long_period,
    return_heatmap=True,
    # n_jobs=1
)
bt.plot()

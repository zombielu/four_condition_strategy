from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import pandas as pd
import numpy as np

class IndicatorDemo(Strategy):
    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume

        # ===== 1. SMA =====
        def SMA(series, n=20):
            return pd.Series(series).rolling(n).mean()

        self.sma = self.I(SMA, close)

        # ===== 2. EMA =====
        def EMA(series, n=20):
            return pd.Series(series).ewm(span=n).mean()

        self.ema = self.I(EMA, close)

        # ===== 3. RSI =====
        def RSI(series, period=14):
            delta = np.diff(series, prepend=series[0])
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)

            avg_gain = pd.Series(gain).rolling(period).mean()
            avg_loss = pd.Series(loss).rolling(period).mean()

            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))

        self.rsi = self.I(RSI, close)

        # ===== 4. MACD =====
        def MACD(series):
            ema12 = pd.Series(series).ewm(span=12).mean()
            ema26 = pd.Series(series).ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            return macd, signal

        self.macd, self.macd_signal = self.I(MACD, close)

        # ===== 5. Bollinger Bands =====
        def BBANDS(series, n=20, k=2):
            s = pd.Series(series)
            ma = s.rolling(n).mean()
            std = s.rolling(n).std()
            upper = ma + k * std
            lower = ma - k * std
            return upper, lower

        self.bb_upper, self.bb_lower = self.I(BBANDS, close)

        # ===== 6. ATR =====
        def ATR(high, low, close, period=14):
            high = pd.Series(high)
            low = pd.Series(low)
            close = pd.Series(close)

            # ✅ 正确的 previous close（无未来函数）
            prev_close = close.shift(1)

            # ✅ True Range 三部分
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # ✅ Wilder 平滑（关键）
            atr = tr.ewm(alpha=1 / period, adjust=False).mean()
            return atr

        self.atr = self.I(ATR, high, low, close)

        # ===== 7. Volume MA =====
        def VOL_MA(x, n=20):
            return pd.Series(x).rolling(n).mean()

        self.vol_ma = self.I(VOL_MA,volume)

        # ===== 8. VWAP =====
        def VWAP(high, low, close, volume):
            typical_price = (high + low + close) / 3
            cum_tp_vol = np.cumsum(typical_price * volume)
            cum_vol = np.cumsum(volume)
            return cum_tp_vol / cum_vol

        self.vwap = self.I(VWAP, high, low, close, volume)

    def next(self):
        # 不做交易，只是跑指标
        pass


bt = Backtest(GOOG, IndicatorDemo, cash=10000)
stats = bt.run()
bt.plot()
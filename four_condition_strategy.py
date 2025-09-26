import pandas as pd
from backtesting import Backtest, Strategy

class FourConditionStrategy(Strategy):
    def init(self):
        self.cond_1_3 = False
        self.time_list = []
        self.curr_time = None
        self.rectangle = []
        self.buy_a2_open = None  # 买入时对应的 a2.open


    def is_valid_time(self, t):
        blocks = {1: (3, 6, 30), 2: (8, 11, 0), 3: (20, 22, 0)}
        for idx, value in blocks.items():
            start_h, end_h, end_m = value
            if (t.hour > start_h or (t.hour == start_h and t.minute >= 0)) and \
                (t.hour < end_h or (t.hour == end_h and t.minute <= end_m)):
                return idx
        return None


    def in_same_block(self, times):
        blocks = [(3, 6, 30), (8, 11, 0), (20, 22, 0)]
        for start_h, end_h, end_m in blocks:
            if all((t.hour > start_h or (t.hour == start_h and t.minute >= 0)) and
                   (t.hour < end_h or (t.hour == end_h and t.minute <= end_m)) for t in times):
                return True
        return False

    def next(self):
        # --- 卖出逻辑 ---
        # print(self.data['time'][-1])
        if self.position:
            # 条件 1: close < a2.open
            if self.data.Close[-1] < self.buy_a2_open:
                self.position.close()
                self.buy_a2_open = None
                return
            # 条件 2: close < MA3
            if (not pd.isna(self.data['Moving Average 3'][-1]) and
                self.data.Close[-1] < self.data['Moving Average 3'][-1]
            ):
                self.position.close()
                self.buy_a2_open = None
                return

        # --- 买入逻辑 ---
        if len(self.data) <= 2:
            return

        # a1, a2, a3 = i - 2, i - 1, i

        # 条件 1: a1.high < a3.low
        # 条件 3: MA1 > MA2 > MA3
        if (self.data.High[-3] < self.data.Low[-1] and
        all([self.data['Moving Average 1'][j] > self.data['Moving Average 2'][j] > self.data['Moving Average 3'][j]
             for j in [-3, -2, -1]])):
            self.curr_time = self.is_valid_time(pd.to_datetime(self.data['time'][-1]))
            self.time_list.extend([pd.to_datetime(self.data['time'][-1]),
                                   pd.to_datetime(self.data['time'][-2]),
                                   pd.to_datetime(self.data['time'][-3])])
            if not self.curr_time or not self.in_same_block(self.time_list):
                self.curr_time = None
                self.time_list = []
                return

            self.cond_1_3 = True
            o1 = self.data.Open[-3]
            c1 = self.data.Close[-3]
            h1 = self.data.High[-3]
            l1 = self.data.Low[-3]
            o2 = self.data.Open[-2]
            c2 = self.data.Close[-2]
            h2 = self.data.High[-2]
            l2 = self.data.Low[-2]
            o3 = self.data.Open[-1]
            c3 = self.data.Close[-1]
            h3 = self.data.High[-1]
            l3 = self.data.Low[-1]
            # ------ only for checking -----------
            ma19 = self.data['Moving Average 1'][-3]
            ma113 = self.data['Moving Average 2'][-3]
            ma121 = self.data['Moving Average 3'][-3]
            ma29 = self.data['Moving Average 1'][-2]
            ma213 = self.data['Moving Average 2'][-2]
            ma221 = self.data['Moving Average 3'][-2]
            ma39 = self.data['Moving Average 1'][-1]
            ma313 = self.data['Moving Average 2'][-1]
            ma321 = self.data['Moving Average 3'][-1]
            self.rectangle.append((o1,c1,h1,l1,o2,c2,h2,l2,o3,c3,h3,l3,ma19,ma113,ma121,ma29,ma213,ma221,ma39,ma313,ma321,self.data['time'][-1]))
            self.time_list = []
            # print("cond1 is True")

        if not self.cond_1_3:
            return

        # 条件 4:
        if self.is_valid_time(
                pd.to_datetime(self.data['time'][-1])) != self.curr_time:
            self.rectangle = []
            self.curr_time = None
            self.cond_1_3 = False
            return

        for related in reversed(self.rectangle):
            # o1, c1, h1, l1, o2, c2, h2, l2, o3, c3, h3, l3 = related
            o1, c1, h1, l1, o2, c2, h2, l2, o3, c3, h3, l3, ma19,ma113,ma121,ma29,ma213,ma221,ma39,ma313,ma321,atime = related
            # case 2
            if self.data.Low[-1] < l3:
                b1_close = self.data.Close[-1]
                b1_open = self.data.Open[-1]
                if b1_open > l3 and b1_close > min(o3, c3):
                    self.buy_a2_open = o2
                    self.buy()
                    print("------case 2---- 4 condition met")
                    print("b1_low:", self.data.Low[-1])
                    print("b1_close:", b1_close)
                    print("b1_open:", b1_open)
                    print("b_time:", self.data['time'][-1])
                    print(related)
                    # raise IndexError
                    return
                # print("cond2 is True")

            # case 1
            if self.data.Low[-2] < l3:
                b2_close = self.data.Close[-1]
                b2_open = self.data.Open[-1]
                b1_close = self.data.Close[-2]
                b1_open = self.data.Open[-2]
                if (b2_close > min(o3, c3) and
                    min(b1_open, b1_close) >= h1 and
                    min(b2_open, b2_close) >= h1):
                    self.buy_a2_open = o2
                    self.buy()
                    print("------case 1---- 4 condition met")
                    print("b1_low:", self.data.Low[-1])
                    print("b1_close:", b1_close)
                    print("b1_open:", b1_open)
                    print("b2_close:", b2_close)
                    print("b2_open:", b2_open)
                    print("b_time:", self.data['time'][-1])
                    print(related)
                    # raise IndexError
                    return
                # print("cond2 is True")



# --- 使用 Backtest ---
# df 是包含 time, open, high, low, close, Moving Average 1/2/3 的 DataFrame
df = pd.read_csv('/Users/weilinwu/Documents/OANDA_XAUUSD, 15_c1cf9.csv')
df = df.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close'
})
bt = Backtest(df, FourConditionStrategy, cash=100000, commission=0.0005, trade_on_close=True)
stats = bt.run()
bt.plot()
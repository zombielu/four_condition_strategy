import pandas as pd
from backtesting import Backtest, Strategy

class FourConditionStrategy(Strategy):
    def init(self):
        self.cond1 = False
        self.cond2 = False
        self.cond3 = False
        self.time_list = []

        # 用于卖出条件
        self.a1_high = None
        self.a2_open = None
        self.a2_close = None
        self.a3_open = None
        self.a3_close = None
        self.a3_low = None
        self.b1_open = None
        self.b1_close = None
        self.b2_close = None
        self.buy_a2_open = None  # 买入时对应的 a2.open

    def clean(self):
        self.cond1 = False
        self.cond2 = False
        self.cond3 = False
        self.time_list = []
        self.a1_high = None
        self.a2_open = None
        self.a2_close = None
        self.a3_open = None
        self.a3_close = None
        self.a3_low = None
        self.b1_open = None
        self.b1_close = None
        self.b2_close = None


    def is_valid_time(self, t):
        blocks = [
            (3, 6, 30),
            (8, 11, 0),
            (20, 22, 0)
        ]
        for start_h, end_h, end_m in blocks:
            if (t.hour > start_h or (t.hour == start_h and t.minute >= 0)) and \
                (t.hour < end_h or (t.hour == end_h and t.minute <= end_m)):
                return True
        return False


    def in_same_block(self, times):
        blocks = [
            (3, 6, 30),
            (8, 11, 0),
            (20, 22, 0)
        ]
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
                print("sell with price: ", self.data.Close[-1])
                self.buy_a2_open = None
                return
            # 条件 2: close < MA3
            if (not pd.isna(self.data['Moving Average 3'][-1]) and
                self.data.Close[-1] < self.data['Moving Average 3'][-1]
            ):
                self.position.close()
                print("sell with price: ", self.data.Close[-1])
                self.buy_a2_open = None
                return

        # --- 买入逻辑 ---
        if len(self.data) <= 2:
            return

        # a1, a2, a3 = i - 2, i - 1, i

        # 条件 1: a1.high < a3.low
        if self.data.High[-3] < self.data.Low[-1]:
            if not self.is_valid_time(pd.to_datetime(self.data['time'][-1])):
                return
            self.cond1 = True
            self.time_list.extend([pd.to_datetime(self.data['time'][-1]),
                                   pd.to_datetime(self.data['time'][-2]),
                                   pd.to_datetime(self.data['time'][-3])])
            self.a1_high = self.data.High[-3]
            self.a2_open = self.data.Open[-2]
            self.a2_close = self.data.Close[-2]
            self.a3_open = self.data.Open[-1]
            self.a3_close = self.data.Close[-1]
            self.a3_low = self.data.Low[-1]
            # print("cond1 is True")

        # 条件 3: MA1 > MA2 > MA3
        if self.cond1 and all([self.data['Moving Average 1'][j] > self.data['Moving Average 2'][j] > self.data['Moving Average 3'][j] for j in [-3, -2, -1]]):
            self.cond3 = True
            # print("cond3 is True")
        else:
            self.clean()

        # 条件 2: 找 b1
        # case 2
        if self.cond1 and self.data.Low[-1] < self.a3_low:
            self.b1_close = self.data.Close[-1]
            if self.b1_close > min(self.a3_open, self.a3_close):
                self.cond2 = True
                self.time_list.append(pd.to_datetime(self.data['time'][-1]))
                # print("cond2 is True")

        if self.cond1 and self.data.Low[-2] < self.a3_low:
            self.b2_close = self.data.Close[-1]
            self.b1_close = self.data.Close[-2]
            self.b1_open = self.data.Open[-2]
            print("min(self.b1_open, self.b1_close)", min(self.b1_open, self.b1_close))
            print("min(self.a2_open, self.a2_close)", min(self.a2_open, self.a2_close))
            if (self.b2_close > min(self.a3_open, self.a3_close) and
                min(self.b1_open, self.b1_close) >= min(self.a2_open, self.a2_close)):
                self.cond2 = True
                self.time_list.extend([pd.to_datetime(self.data['time'][-1]),
                                       pd.to_datetime(self.data['time'][-2])])
                # print("cond2 is True")
        if not self.cond2:
            self.clean()


        # 条件 4: 三根 bar 在同一 block
        if self.cond1 and self.cond2 and self.cond3:
            print("this day met all 3 conditions: ", self.data['time'][-1])
            print("self.a1_high: ", self.a1_high,
                  "self.a2_open:", self.a2_open,
                  "self.a2_close:", self.a2_close,
                  "self.a3_open:", self.a3_open,
                  "self.a3_close:", self.a3_close,
                  "self.a3_low:", self.a3_low,
                  "self.b1_open:", self.b1_open,
                  "self.b1_close:", self.b1_close,
                  "self.b2_close:", self.b2_close,
                  "time_list:", self.time_list,
                  )


            if not self.in_same_block(self.time_list):
                self.clean()
            else:
                self.buy()
                self.buy_a2_open = self.a2_open
                print("cond4 is True, buy in with price: ", self.buy_a2_open)

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
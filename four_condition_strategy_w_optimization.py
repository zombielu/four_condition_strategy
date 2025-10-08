from datetime import datetime
import pandas as pd
from backtesting import Backtest, Strategy


class FourConditionStrategy(Strategy):
    # n_jobs = 1  # declare parallel optimization here, 1 means non-parallel
    short_period = 7
    mid_period = 11
    long_period = 15

    def init(self):
        self.cond_1_3 = False
        self.time_list = []
        self.curr_time = None
        self.rectangle = []
        self.buy_a2_open = None  # 买入时对应的 a2.open

        def ema(series, period):
            return pd.Series(series).ewm(span=period, adjust=False).mean()

        # 注册三个 EMA 指标
        self.ema_short = self.I(ema, self.data.Close, self.short_period)
        self.ema_mid = self.I(ema, self.data.Close, self.mid_period)
        self.ema_long = self.I(ema, self.data.Close, self.long_period)

    def is_valid_time(self, t: datetime) -> int | None:
        """
        Determine which predefined time block a given datetime falls into.
        The method checks if the provided datetime `t` falls within one of three time blocks:
        1. Block 1: 03:00–06:30
        2. Block 2: 08:00–11:00
        3. Block 3: 20:00–22:00
        Each block is defined by a start hour, end hour, and end minute.
        If the time `t` falls within a block (inclusive of boundaries), the
        corresponding block index is returned.

        Args:
            t: The datetime object to check.

        Returns:
            The index of the matching time block (1, 2, or 3),
            or None if `t` does not fall into any block.

        """
        blocks = {1: (3, 6, 30), 2: (8, 11, 0), 3: (20, 22, 0)}
        for idx, value in blocks.items():
            start_h, end_h, end_m = value
            if (t.hour > start_h or (t.hour == start_h and t.minute >= 0)) and \
                (t.hour < end_h or (t.hour == end_h and t.minute <= end_m)):
                return idx
        return None


    def in_same_block(self, times: list[datetime]) -> bool:
        """
        Check whether all given datetime objects fall within the same predefined time block.
        The three fixed time blocks:
        1. 03:00–06:30
        2. 08:00–11:00
        3. 20:00–22:00
        If all datetimes in `times` fall within any one of these blocks (inclusive of boundaries),
        the method returns True. Otherwise, it returns False.

        Args:
            times: A list of datetime objects to check.

        Returns:
            True if all datetimes fall within the same block, False otherwise.

        """
        blocks = [(3, 6, 30), (8, 11, 0), (20, 22, 0)]
        for start_h, end_h, end_m in blocks:
            if all((t.hour > start_h or (t.hour == start_h and t.minute >= 0)) and
                   (t.hour < end_h or (t.hour == end_h and t.minute <= end_m)) for t in times):
                return True
        return False

    def next(self):
        # --- sell ---
        if self.position:
            # case 1: close < a2.open
            if self.data.Close[-1] < self.buy_a2_open:
                self.position.close()
                self.buy_a2_open = None
                return
            # case 2: close < MA3
            if (not pd.isna(self.ema_long[-1]) and
                self.data.Close[-1] < self.ema_long[-1]
            ):
                self.position.close()
                self.buy_a2_open = None
                return

        # --- buy ---
        if len(self.data) <= 2:
            return

        # condition 1: a1.high < a3.low
        # condition 3: MA1 > MA2 > MA3
        if (self.data.High[-3] < self.data.Low[-1] and
        all([self.ema_short[j] > self.ema_mid[j] > self.ema_long[j]
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

            self.rectangle.append((o1,c1,h1,l1,o2,c2,h2,l2,o3,c3,h3,l3,self.data['time'][-1]))
            self.time_list = []

        if not self.cond_1_3:
            return

        # condition 4: condition 1,2,3 must happen within the same time block.
        if self.is_valid_time(
                pd.to_datetime(self.data['time'][-1])) != self.curr_time:
            self.rectangle = []
            self.curr_time = None
            self.cond_1_3 = False
            return

        # condition 2:
        for related in reversed(self.rectangle):
            o1, c1, h1, l1, o2, c2, h2, l2, o3, c3, h3, l3, time = related
            # case 2
            if self.data.Low[-1] < l3:
                b1_close = self.data.Close[-1]
                b1_open = self.data.Open[-1]
                if b1_open > l3 and b1_close > min(o3, c3):
                    self.buy_a2_open = o2
                    self.buy()
                    # print("------case 2---- 4 condition met")
                    # print("b1_low:", self.data.Low[-1])
                    # print("b1_close:", b1_close)
                    # print("b1_open:", b1_open)
                    # print("b_time:", self.data['time'][-1])
                    # print(related)
                    # raise IndexError
                    return

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
                    # print("------case 1---- 4 condition met")
                    # print("b1_low:", self.data.Low[-1])
                    # print("b1_close:", b1_close)
                    # print("b1_open:", b1_open)
                    # print("b2_close:", b2_close)
                    # print("b2_open:", b2_open)
                    # print("b_time:", self.data['time'][-1])
                    # print(related)
                    # raise IndexError
                    return




# --- Backtest ---
df = pd.read_csv(
    '/Users/weilinwu/Documents/OANDA_XAUUSD, 15_c1cf9.csv',
    usecols=['open', 'high', 'low', 'close', 'time']  # only load these columns
)
df = df.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close'
})
# The buffer of bt.optimize only accept 2048 = 2^11 rows of records,
# if it is good enough for you, use the following code to do the optimization.
# df = df.iloc[-2000:]
# bt = Backtest(df, FourConditionStrategy, cash=100000, commission=0, trade_on_close=True)
# stats = bt.optimize(
#     short_period=range(5, 17, 2),
#     mid_period=range(9, 23, 2),
#     long_period=range(15, 31, 2),
#     maximize='Equity Final [$]',
#     constraint=lambda p: p.short_period < p.mid_period < p.long_period,
#     # n_jobs=1  # non-parallel
#     # Note: even with non-parallel, bt still copy df for each parameter combination,
#     # so n_jobs=1 doesn't help. I put it here only to mention this method doesn't work!
# )

# In order to use all the data to do optimization, use for loops below.
# After find the best parameter combination, comment out code below and rerun the code
# with the best parameter to plot the trades.
# best = (0, 0, 0, 0)
# for short in range(3, 17, 2):
#     for mid in range(5, 23, 2):
#         for long in range(5, 31, 2):
#             if short >= mid or mid >= long or short >= long:
#                 continue
#             bt = Backtest(df, FourConditionStrategy, cash=100000, commission=0,trade_on_close=True)
#             stats = bt.run(short_period=short, mid_period=mid, long_period=long)
#             if stats['Equity Final [$]'] > best[0]:
#                 best = (stats['Equity Final [$]'], short, mid, long)
# print(best)

# After find the best, use the best parameters run the following code to plot the trades.
bt = Backtest(df, FourConditionStrategy, cash=100000, commission=0, trade_on_close=True)
stats = bt.run()
print(stats)
bt.plot()
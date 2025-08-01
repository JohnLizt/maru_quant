import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from indicator.CandleStrengthIndex import CandleStrengthIndex
import backtrader as bt

def test_bt_indicator():
    print("\nBacktrader Indicator tests:")

    class TestData(bt.feeds.PandasData):
        lines = ('open', 'high', 'low', 'close',)
        params = (('datetime', None),)

    import pandas as pd
    df = pd.DataFrame([
        {'open': 10, 'high': 12, 'low': 8, 'close': 12},   # Hammer
        {'open': 10, 'high': 12, 'low': 8, 'close': 8},   # Inverted Hammer
        {'open': 10, 'high': 12, 'low': 9, 'close': 9},     # Doji
        {'open': 10, 'high': 15, 'low': 10, 'close': 15},    # Big Bullish
        {'open': 15, 'high': 15, 'low': 10, 'close': 10},    # Big Bearish
        {'open': 10, 'high': 15, 'low': 9, 'close': 10.5},   # Shooting Star
    ])
    df.index = pd.date_range('2020-01-01', periods=len(df), freq='D')

    class CSITestStrategy(bt.Strategy):
        def __init__(self):
            self.csi = CandleStrengthIndex()

        def next(self):
            dt = self.datas[0].datetime.date(0)
            print(f"{dt}: {self.csi[0]:.4f}")

    cerebro = bt.Cerebro()
    data = TestData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(CSITestStrategy)
    cerebro.run()

if __name__ == "__main__":
    test_bt_indicator()

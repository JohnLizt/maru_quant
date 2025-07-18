import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicator.CandleStrengthIndex import candle_strength_index

def test_candle_strength_index():
    # 锤型线（Hammer）：下影长，上影短，收盘高于开盘
    print("Hammer:", candle_strength_index(open=10, high=11, low=8, close=10.8))

    # 星型线（Doji）：开盘价≈收盘价，上下影线长
    print("Doji:", candle_strength_index(open=10, high=12, low=8, close=10))

    # 大阳线：收盘远高于开盘，无影线
    print("Big Bullish:", candle_strength_index(open=10, high=15, low=10, close=15))

    # 大阴线：收盘远低于开盘，无影线
    print("Big Bearish:", candle_strength_index(open=15, high=15, low=10, close=10))

    # 上影线长（Shooting Star）：开盘高，收盘低，下影短
    print("Shooting Star:", candle_strength_index(open=10, high=15, low=9, close=10.5))

    # 下影线长（Inverted Hammer）：开盘低，收盘高，上影短
    print("Inverted Hammer:", candle_strength_index(open=10, high=11, low=7, close=10.9))

if __name__ == "__main__":
    test_candle_strength_index()

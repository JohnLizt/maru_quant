import backtrader as bt
import pandas as pd
import logging

from indicator.PivotHigh import PivotHigh
from strategy.trendtracking.breakout import PivotBreakout
from utils.logger import setup_strategy_logger

# Create a Strategy
class SmoothedPivotBreakout(PivotBreakout):
    params = (
        ('window', 16),  # 滑动窗口大小（影响resist的灵敏度，窗口越小，resist数量越多）
        ('max_resists', 5),  # 最多同时保存的阻力位数量
        ('resist_zone_width', 0.01),  # 阻力带宽度，单位为ATR倍数
        ('sma_period', 30),  # 均线周期，默认20
        ('max_hold_bars', 36),   # 最大持仓时间，默认24 = 12小时，可以设 -1 无限期持仓
        ('take_profit_atr', 7),  # 止盈ATR倍数，默认2倍ATR
        ('stop_loss_atr', 10),    # 止损ATR倍数，默认1.5倍ATR
        ('atr_period', 14),        # ATR周期，默认14
    )

    def __init__(self):
        super().__init__()  # 调用父类的初始化方法

    def break_signal(self):
        """Check if the current price breaks the resistance level"""
        # 动态生成阻力线列表，根据max_resisst参数
        for i in range(self.params.max_resists):
            resist_name = f'resist{i}'
            resist_value = getattr(self.resistance.lines, resist_name)[0]
            upper_bound = resist_value + self.atr[0] * self.p.resist_zone_width 
            if not pd.isna(resist_value) and self.ema[-1] < upper_bound < self.ema[0]:
                self.logger.info(f'[↑↑SIG↑↑]：均线突破阻力位 {resist_value:.2f}, 均线价格 {self.ema[0]:.2f}，执行买入')
                return True
        return False
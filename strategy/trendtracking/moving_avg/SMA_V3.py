import backtrader as bt
import numpy as np
from utils.logger import setup_strategy_logger

class SMA_V3(bt.Strategy):
    """高级SMA策略 - 包含多时间框架和自适应参数"""
    
    params = (
        ('ma_short', 10),
        ('ma_medium', 20), 
        ('ma_long', 50),
        ('lookback_period', 20),    # 用于计算自适应参数
        ('volatility_threshold', 0.02),  # 波动率阈值
        ('trend_strength_min', 0.6),     # 最小趋势强度
        ('max_hold_days', 30),           # 最大持仓天数
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.entry_bar = None
        
        # 多重均线系统
        self.ma_short = bt.indicators.SMA(self.datas[0], period=self.params.ma_short)
        self.ma_medium = bt.indicators.SMA(self.datas[0], period=self.params.ma_medium)
        self.ma_long = bt.indicators.SMA(self.datas[0], period=self.params.ma_long)
        
        # 自适应指标
        self.atr = bt.indicators.ATR(self.datas[0], period=14)
        
        # 趋势强度指标
        self.adx = bt.indicators.AverageDirectionalIndex(self.datas[0], period=14)
        
        self.logger = setup_strategy_logger(self, __name__, "INFO")
    
    def calculate_trend_strength(self):
        """计算趋势强度"""
        if len(self.ma_short) < self.params.lookback_period:
            return 0
            
        # 计算均线方向一致性
        short_slope = (self.ma_short[0] - self.ma_short[-5]) / 5
        medium_slope = (self.ma_medium[0] - self.ma_medium[-5]) / 5
        long_slope = (self.ma_long[0] - self.ma_long[-5]) / 5
        
        # 趋势一致性得分
        slopes = [short_slope, medium_slope, long_slope]
        positive_slopes = sum(1 for slope in slopes if slope > 0)
        negative_slopes = sum(1 for slope in slopes if slope < 0)
        
        consistency = max(positive_slopes, negative_slopes) / len(slopes)
        
        # 结合ADX
        adx_strength = min(self.adx[0] / 50, 1.0)  # 归一化ADX
        
        return consistency * adx_strength
    
    def calculate_volatility(self):
        """计算近期波动率"""
        if len(self.dataclose) < self.params.lookback_period:
            return 0
            
        returns = []
        for i in range(1, self.params.lookback_period + 1):
            ret = (self.dataclose[0] - self.dataclose[-i]) / self.dataclose[-i]
            returns.append(ret)
            
        return np.std(returns)
    
    def is_market_condition_favorable(self):
        """判断市场条件是否有利"""
        volatility = self.calculate_volatility()
        trend_strength = self.calculate_trend_strength()
        
        # 中等波动率 + 强趋势 = 有利条件
        volatility_ok = volatility > 0.005 and volatility < self.params.volatility_threshold
        trend_ok = trend_strength > self.params.trend_strength_min
        
        return volatility_ok and trend_ok
    
    def next(self):
        if self.order or len(self.dataclose) < max(self.params.ma_long, self.params.lookback_period):
            return
            
        # 检查市场条件
        if not self.is_market_condition_favorable():
            return
            
        if not self.position:
            # 三重均线确认买入信号
            if (self.ma_short[0] > self.ma_medium[0] > self.ma_long[0] and
                self.dataclose[0] > self.ma_short[0] and
                self.calculate_trend_strength() > self.params.trend_strength_min):
                
                self.logger.info(f'[BUY] 趋势强度: {self.calculate_trend_strength():.3f}, '
                               f'波动率: {self.calculate_volatility():.4f}')
                self.order = self.buy()
                self.entry_bar = len(self)
                
        else:
            # 退出条件
            bars_held = len(self) - self.entry_bar
            
            # 1. 均线转向
            trend_reversal = (self.ma_short[0] < self.ma_medium[0] or 
                            self.dataclose[0] < self.ma_short[0])
            
            # 2. 趋势强度下降
            weak_trend = self.calculate_trend_strength() < 0.3
            
            # 3. 超时退出
            timeout = bars_held > self.params.max_hold_days
            
            if trend_reversal or weak_trend or timeout:
                reason = ("趋势转向" if trend_reversal else 
                         "趋势减弱" if weak_trend else "超时退出")
                self.logger.info(f'[SELL] 原因: {reason}, 持仓: {bars_held}天')
                self.order = self.sell()
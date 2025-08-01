import backtrader as bt
import numpy as np
import math
from backtrader import TimeFrame
from backtrader.analyzers import TimeReturn
from backtrader.mathsupport import average, standarddev
from backtrader.utils.py3 import itervalues

class SharpeRatio_30min(bt.Analyzer):
    params = (
        ('riskfreerate', 0.0),  # 无风险利率（黄金交易通常设为0）
        ('factor', 252 * 23 * 2),  # 30分钟年化因子：252个交易日 * 23小时 * 2个30分钟
        ('annualize', True),  # 是否年化
        ('stddev_sample', False),  # 贝塞尔校正
    )
    
    def __init__(self):
        # 使用30分钟时间框架的TimeReturn分析器
        self.timereturn = TimeReturn(
            timeframe=TimeFrame.Minutes,
            compression=30,
            fund=None
        )
        
    def start(self):
        # 初始化结果字典
        self.rets = {}
        
    def stop(self):
        super(SharpeRatio_30min, self).stop()
        
        # 从TimeReturn分析器获取收益率
        returns = list(itervalues(self.timereturn.get_analysis()))
        
        rate = self.p.riskfreerate
        factor = self.p.factor
        
        # 检查是否有足够的数据计算
        lrets = len(returns) - self.p.stddev_sample
        
        if lrets <= 0:
            # 没有足够的收益数据
            ratio = None
        else:
            try:
                # 计算超额收益
                ret_free = [r - rate for r in returns]
                ret_free_avg = average(ret_free)
                retdev = standarddev(ret_free, avgx=ret_free_avg,
                                   bessel=self.p.stddev_sample)
                
                if retdev == 0:
                    ratio = None
                else:
                    ratio = ret_free_avg / retdev
                    
                    # 如果需要年化
                    if factor is not None and self.p.annualize:
                        ratio = math.sqrt(factor) * ratio
                        
            except (ValueError, TypeError, ZeroDivisionError):
                ratio = None
        
        self.ratio = ratio
        self.rets['sharperatio'] = self.ratio
        
    def get_analysis(self):
        """返回夏普率分析结果"""
        return self.rets
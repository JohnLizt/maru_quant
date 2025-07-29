import backtrader as bt
import pandas as pd
import logging

from indicator.PivotHigh import PivotHigh
from strategy.utils.bracketorder import cancel_bracket_orders, create_bracket_orders
from utils.logger import setup_strategy_logger

# Create a Stratey
class SimpleBreakout(bt.Strategy):
    params = (
        ('window', 12),  # 滑动窗口大小（影响resist的密集程度，窗口越小，resist越密集）
        ('threshold', 0.001),  # 区间阈值，默认0.1%（影响resist的密集程度，区间定义越宽，resist越密集）
        ('max_hold_bars', 24),   # 最大持仓时间，默认24, 12小时
        ('take_profit', 30),  # 止盈价格差，默认30个价格点
        ('stop_loss', 15),    # 止损价格差，默认15个价格点
        ('sma_period', 20),  # 均线周期，默认20
    )

    def __init__(self):
        self.resistance = PivotHigh(self.data, window=self.params.window, threshold=self.params.threshold)
        # self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)
        self.ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.sma_period)
        
        self.dataclose = self.datas[0].close
        self.entry_bar = None  # 记录开仓的bar索引
        self.bracket_orders = []  # 存储bracket订单对象

        self.logger = setup_strategy_logger(self, __name__, "INFO")

    def next(self):
        self.logger.debug(f'LOG: Price: {self.dataclose[0]:.2f}, Position: {self.position.size}, Orders: {len(self.bracket_orders)} Cash: {self.broker.getcash():.2f}')
        if not self.position:
            if self.bracket_orders:
                self.logger.info(f'ORDER PENDING, skip next') # 下市价单，一般不会走到这
                return

            if self.break_signal():
                self.bracket_orders = create_bracket_orders(self)
                self.entry_bar = len(self)  # 记录开仓的bar索引
        else:
            # 超过最大持仓时间，强制平仓 (仅当max_hold_bars > 0时生效)
            if (self.params.max_hold_bars > 0 and 
                self.entry_bar is not None and 
                len(self) - self.entry_bar >= self.params.max_hold_bars):
                self.logger.info(f'[信号]：超过最大持仓时间 {self.params.max_hold_bars}, 强制平仓')
                cancel_bracket_orders(self)
                self.close()
                self.entry_bar = None
                return


    def notify_order(self, order):
        self.logger.debug('Order {}, Price: {}, Type: {}, Status: {}'.format(order.ref, order.executed.price if order.executed.price else order.price, 'Buy' * order.isbuy() or 'Sell', order.getstatusname()))
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            # 打印日志
            comminfo = self.broker.getcommissioninfo(self.data)
            margin = comminfo.get_margin(order.executed.price)
            if order.isbuy():
                self.logger.info('BUY EXECUTED, Price: %.2f, Size: %.2f Lot, Margin: %.2f, Comm %.2f, CASH %.2f' %
                    (order.executed.price, order.executed.size, margin, order.executed.comm, self.broker.getcash()))
            else: 
                self.logger.info('SELL EXECUTED, Price: %.2f, Size: %.2f Lot, Margin: %.2f, Comm %.2f, CASH %.2f' %
                    (order.executed.price, order.executed.size, margin, order.executed.comm, self.broker.getcash()))

        # elif order.status in [order.Canceled, order.Margin, order.Rejected]:

        # 清理已完成或取消的订单
        if not order.alive() and order in self.bracket_orders:
            self.bracket_orders.remove(order)


    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.logger.info('TRADE DONE, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def break_signal(self):
        """Check if the current price breaks the resistance level"""
        resist_lines = ['resist0', 'resist1', 'resist2', 'resist3', 'resist4']
        for resist_name in resist_lines:
            resist_value = getattr(self.resistance.lines, resist_name)[0]
            if not pd.isna(resist_value) and self.ema[-1] < resist_value < self.ema[0]:
                self.logger.info(f'[信号]：均线突破阻力位 {resist_value:.2f}, 均线价格 {self.ema[0]:.2f}，执行买入')
                return True
        return False

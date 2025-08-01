import backtrader as bt
import pandas as pd
import logging

from maru_quant.indicator.PivotHigh import PivotHigh
from maru_quant.utils.logger import setup_strategy_logger

# Create a Strategy
class PivotBreakout(bt.Strategy):
    params = (
        ('window', 16),  # 滑动窗口大小（影响resist的灵敏度，窗口越小，resist数量越多）
        ('max_resists', 5),  # 最多同时保存的阻力位数量
        ('max_hold_bars', 36),   # 最大持仓时间，默认24 = 12小时，可以设 -1 无限期持仓
        ('take_profit_atr', 7),  # 止盈ATR倍数，默认2倍ATR
        ('stop_loss_atr', 10),    # 止损ATR倍数，默认1.5倍ATR
        ('atr_period', 14),        # ATR周期，默认14
        ('sma_period', 30),  # 均线周期，默认20
    )

    def __init__(self):
        self.resistance = PivotHigh(self.data, window=self.params.window, max_resists=self.params.max_resists)
        # self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)
        self.ema = bt.indicators.ExponentialMovingAverage(self.data.close, period=self.params.sma_period)
        
        # Add ATR indicator for dynamic stop loss and take profit
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        self.dataclose = self.datas[0].close
        self.entry_bar = None  # 记录开仓的bar索引
        self.bracket_orders = []  # 存储bracket订单对象

        self.logger = setup_strategy_logger(self, __name__, "INFO")

    def next(self):
        self.logger.debug(f'LOG: Price: {self.dataclose[0]:.2f}, Position: {self.position.size}, Orders: {len(self.bracket_orders)} Cash: {self.broker.getcash():.2f}, ATR: {self.atr[0]:.2f}')
        if not self.position:
            if self.bracket_orders:
                self.logger.info(f'ORDER PENDING, skip next') # 下市价单，一般不会走到这
                return

            if self.break_signal():
                stop_loss_price, take_profit_price = self.get_atr_levels()
                self.logger.info(f'[多单]：当前价格 {self.dataclose[0]:.2f}，止盈价格 {take_profit_price:.2f}，止损价格 {stop_loss_price:.2f}')
                self.bracket_orders = self.buy_bracket(exectype=bt.Order.Market, stopprice=stop_loss_price, limitprice=take_profit_price)
        else:
            # 超过最大持仓时间，强制平仓
            if (self.params.max_hold_bars > 0 and self.entry_bar is not None and len(self) - self.entry_bar >= self.params.max_hold_bars):
                self.logger.info(f'[信号]：超过最大持仓时间 {self.params.max_hold_bars}, 强制平仓')
                self.close()
                self.cancel_bracket_orders()
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
                self.entry_bar = len(self)  # 记录开仓的bar索引
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

        self.logger.info('===== TRADE DONE, GROSS %.2f, NET %.2f =====' %
                 (trade.pnl, trade.pnlcomm))

    def break_signal(self):
        """Check if the current price breaks the resistance level"""
        # 动态生成阻力线列表，根据max_resisst参数
        for i in range(self.params.max_resists):
            resist_name = f'resist{i}'
            resist_value = getattr(self.resistance.lines, resist_name)[0]
            if not pd.isna(resist_value) and self.ema[-1] < resist_value < self.ema[0]:
                self.logger.info(f'[↑↑SIG↑↑]：均线突破阻力位 {resist_value:.2f}, 均线价格 {self.ema[0]:.2f}，执行买入')
                return True
        return False

    def get_atr_levels(self):
        """Calculate ATR-based stop loss and take profit levels"""
        entry_price = self.dataclose[0]
        current_atr = self.atr[0]
        stop_loss_price = entry_price - (current_atr * self.params.stop_loss_atr)
        take_profit_price = entry_price + (current_atr * self.params.take_profit_atr)
        return stop_loss_price, take_profit_price
    
    def cancel_bracket_orders(self):
        """取消所有bracket订单"""
        for order in self.bracket_orders[:]:  # 使用切片复制列表避免修改时出错
            if order and order.status in [order.Submitted, order.Accepted, order.Partial]:
                self.cancel(order)
        self.bracket_orders = []  # 清空列表

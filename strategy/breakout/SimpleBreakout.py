import backtrader as bt
import pandas as pd

from indicator.PivotHigh import PivotHigh
from strategy.utils.TakeProfitStopLoss import takeProfitStopLoss

# Create a Stratey
class SimpleBreakout(bt.Strategy):
    params = (
        ('window', 16),  # 滑动窗口大小（影响resist的密集程度，窗口越小，resist越密集）
        ('threshold', 0.001),  # 区间阈值，默认0.1%（影响resist的密集程度，区间定义越宽，resist越密集）
        ('max_hold_bars', 24),   # 最大持仓时间，默认24个bar
        ('take_profit', 0.008),  # 止盈率，默认0.5%
        ('stop_loss', 0.003),    # 止损率，默认0.25%
        ('sma_period', 10),  # 均线周期，默认20
    )

    def __init__(self):
        self.resistance = PivotHigh(self.data, window=self.params.window, threshold=self.params.threshold)
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)

        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # 检查所有阻力位是否被突破
            resist_lines = ['resist0', 'resist1', 'resist2', 'resist3', 'resist4']
            for resist_name in resist_lines:
                resist_value = getattr(self.resistance.lines, resist_name)[0]
                
                # 如果阻力位有效且日内突破（开盘价 < 阻力位，收盘价 > 阻力位）
                if not pd.isna(resist_value) and self.sma[-1] < resist_value < self.sma[0]:
                    self.log(f'[信号]：均线突破阻力位 {resist_name}={resist_value:.2f}， 均线价格 {self.sma[0]:.2f}，执行买入')
                    self.order = self.buy()
                    break  # 只要有一个阻力位被突破就执行买入
        else:
            # 使用公共的持仓管理逻辑
            takeProfitStopLoss(self, take_profit=self.params.take_profit, stop_loss=self.params.stop_loss)

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime[0]
        print('%s, %s' % (bt.num2date(dt).strftime('%Y-%m-%d %H:%M:%S'), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %.0f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Size: %.0f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.size,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
    
    def stop(self):
        # print params
        self.log('Strategy Parameters:')
        for param, value in self.params._getkwargs().items():
            self.log(f'{param}: {value}')
        # print final value
        self.log('Ending Value %.2f' % self.broker.getvalue())


import backtrader as bt
import pandas as pd
from indicator.CandleStrengthIndex import CandleStrengthIndex
from indicator.PivotHigh import PivotHigh, PivotLow

# 定义支撑位/阻力位突破策略
class Macky(bt.Strategy):
    params = (
        ('window', 2),  # 支撑/阻力位计算窗口大小
        ('hold_days', 5),  # 最大持仓周期
        ('observe_period', 2), # 观察周期
        ('CSI_threshold', 0.5),  # 买入强度阈值
        ('take_profit', 0.1),    # 止盈点（10%）
        ('stop_loss', 0.05),     # 止损点（5%）
        ('stake_size', 10), # 每次交易的股数
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime[0]
        print('%s, %s' % (bt.num2date(dt).strftime('%Y-%m-%d %H:%M:%S'), txt))
    
    def __init__(self):
        # 用PivotHigh/PivotLow替换原有支撑阻力指标
        self.resistance = PivotHigh(self.data, window=self.params.window)
        self.support = PivotLow(self.data, window=self.params.window)
        self.order = None
        self.entry_bar = None  # 记录开仓的bar号
        self.break_bar = None  # 记录突破阻力/支撑位的bar号
        self.csi = CandleStrengthIndex(self.data) # 蜡烛强度指标
        self.csi.plotinfo.plot = False  # 不在图表中显示CSI

    def next(self):
        # 如果有未完成订单，跳过
        if self.order:
            return
        
        # 最后一天不做交易，防止越界
        if len(self.data) - self.data._minperiod == self.datas[0].buflen() - 1:
            return

        # 开单逻辑
        if not self.position and self.break_bar is not None:
            break_bar = len(self) - self.break_bar
            # 1. 如果超出观察周期：取消等待
            if break_bar > self.params.observe_period:
                self.log('观察周期结束, 取消等待')
                self.break_bar = None
                return
            strength = self.csi[0]
            self.log(f'观察中... CSI={strength:.2f}')
            # 2. 如果CSI大于阈值，开多单
            if strength >= self.params.CSI_threshold:
                self.order = self.buy()
                self.entry_bar = len(self)
                # print(f'{bt.num2date(self.data.datetime[1])}, 【开多单】: 价格: {self.data.open[1]}, 前收盘价: {self.data.close[0]}, 阻力位: {self.resistance[0]}')
                self.break_bar = None
            # 3. 如果CSI小于等于阈值，开空单
            if strength <= -self.params.CSI_threshold:
                self.order = self.sell()
                self.entry_bar = len(self)
                # print(f'{bt.num2date(self.data.datetime[1])}, 【开空单】: 价格: {self.data.open[1]}, 前收盘价: {self.data.close[0]}, 支撑位: {self.support[0]}')
                self.break_bar = None
            return

        # 平仓逻辑
        if self.position:
            holding_days = len(self) - self.entry_bar
            entry_price = self.position.price
            current_price = self.data.close[0]
            # 修正利润率计算：多单为(现价-开仓价)/开仓价，空单为(开仓价-现价)/开仓价
            if self.position.size > 0:
                profit_rate = (current_price - entry_price) / entry_price
            else:
                profit_rate = (entry_price - current_price) / entry_price
            profit_rate = profit_rate * self.params.stake_size
            closed = False
            # 止盈
            if profit_rate >= self.params.take_profit:
                self.log(f'【止盈平仓】: 当前价格: {self.data.open[1]}, 前收盘价: {current_price}, 利润率: {profit_rate:.2%}')
                closed = True
            # 止损
            elif profit_rate <= -self.params.stop_loss:
                self.log(f'【止损平仓】: 当前价格: {self.data.open[1]}, 前收盘价: {current_price}, 利润率: {profit_rate:.2%}')
                closed = True
            # 超过持仓周期
            elif holding_days >= self.params.hold_days:
                self.log(f'【到期平仓】: 当前价格: {self.data.open[1]}, 前收盘价: {current_price}, 利润率: {profit_rate:.2%}')
                closed = True

            if closed:
                self.close()
                self.entry_bar = None
                return
            self.log(f'持仓中... 当日收盘价: {current_price}, 利润率: {profit_rate:.2%}, 持仓时长: {holding_days}')
            return  # 平仓后本bar不再开新仓

        # 信号：突破阻力位逻辑
        if self.resistance.lines.breakout[0] == 1:
            self.break_bar = len(self)
            self.log(f'突破阻力位，开始观察: 当前价格: {self.data.close[0]}, 阻力位: {self.resistance[0]}')
            return

        # 信号：跌破支撑位逻辑
        if self.support.lines.breakdown[0] == 1:
            self.break_bar = len(self)
            self.log(f'跌破支撑位，开始观察: 当前价格: {self.data.close[0]}, 支撑位: {self.support[0]}')
            return

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        
        if order.status in [order.Completed]:
            # 判断是否为平仓操作：检查订单执行前的持仓状态
            was_positioned = hasattr(self, '_was_positioned') and self._was_positioned
            
            if not was_positioned:  # 只有开仓操作才打印
                if order.isbuy():
                    self.log(f"【开多单】，价格: {order.executed.price}, 数量: {order.executed.size}")
                elif order.issell():
                    self.log(f"【开空单】，价格: {order.executed.price}, 数量: {order.executed.size}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f"平仓，利润: {trade.pnl:.2f}, 手续费: {trade.commission:.2f}")
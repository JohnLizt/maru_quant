import backtrader as bt
import pandas as pd
from indicator.CandleStrengthIndex import CandleStrengthIndex

# 定义支撑位/阻力位突破策略
class SupportResistanceBreakout(bt.Strategy):
    params = (
        ('period', 20),  # 计算支撑位和阻力位的周期
        ('hold_days', 5),  # 最大持仓周期
        ('observe_period', 2), # 观察周期
        ('CSI_threshold', 0.5),  # 买入强度阈值
        ('take_profit', 0.1),    # 止盈点（10%）
        ('stop_loss', 0.05),     # 止损点（5%）
        ('stake_size', 10), # 每次交易的股数
    )
    
    def __init__(self):
        # 定义支撑位和阻力位，subplot=False 画在主图
        self.support = bt.indicators.Lowest(self.data.low(-1), period=self.params.period, subplot=False)
        self.resistance = bt.indicators.Highest(self.data.high(-1), period=self.params.period, subplot=False)
        self.order = None
        self.entry_bar = None  # 记录开仓的bar号
        self.break_bar = None  # 记录突破阻力/支撑位的bar号
        self.csi = CandleStrengthIndex(self.data)

    def next(self):
        # 如果有未完成订单，跳过
        if self.order:
            return

        # 平仓逻辑：持有多单或空单达到指定天数或止盈止损则平仓
        if self.position:
            if self.entry_bar is not None:
                holding_days = len(self) - self.entry_bar
                entry_price = self.position.price
                current_price = self.data.close[0]
                # 修正利润率计算：多单为(现价-开仓价)/开仓价，空单为(开仓价-现价)/开仓价
                if self.position.size > 0:
                    profit_rate = (current_price - entry_price) / entry_price
                else:
                    profit_rate = (entry_price - current_price) / entry_price
                profit_rate = profit_rate * self.params.stake_size
                dt_str = bt.num2date(self.data.datetime[0]).strftime('%Y-%m-%d %H:%M:%S')
                closed = False
                # 止盈
                if profit_rate >= self.params.take_profit:
                    # 注意backtrader的订单是下一个bar才会成交
                    print(f'{bt.num2date(self.data.datetime[1])}, 【止盈平仓】: 当前价格: {self.data.open[0]}, 前收盘价: {current_price}, 预期利润率: {profit_rate:.2%}')
                    closed = True
                # 止损
                elif profit_rate <= -self.params.stop_loss:
                    print(f'{bt.num2date(self.data.datetime[1])}, 【止损平仓】: 当前价格: {self.data.open[0]}, 前收盘价: {current_price}, 预期利润率: {profit_rate:.2%}')
                    closed = True
                # 超过持仓周期
                elif holding_days >= self.params.hold_days:
                    print(f'{bt.num2date(self.data.datetime[1])}, 【到期平仓】: 当前价格: {self.data.open[0]}, 前收盘价: {current_price}, 利润率: {profit_rate:.2%}')
                    closed = True

                if closed:
                    # 只负责平仓，不再统计胜率等
                    self.close()
                    self.entry_bar = None
                    return
                print(f'{bt.num2date(self.data.datetime[0])} 持仓中... 当日收盘价: {current_price}, 利润率: {profit_rate:.2%}, 持仓时长: {holding_days}')
            return  # 平仓后本bar不再开新仓

        # 开单逻辑
        if self.break_bar is not None:
            break_bar = len(self) - self.break_bar
            # 1. 如果超出观察周期：取消等待
            if break_bar > self.params.observe_period:
                print(f'{bt.num2date(self.data.datetime[0])} 观察周期结束, 取消等待')
                self.break_bar = None
                return
            strength = self.csi[0]
            print(f'{bt.num2date(self.data.datetime[0])} 观察中... CSI={strength:.2f}')
            # 2. 如果CSI大于阈值，开多单
            if strength >= self.params.CSI_threshold:
                self.order = self.buy()
                self.entry_bar = len(self)
                print(f'{bt.num2date(self.data.datetime[1])}, 【开多单】: 价格: {self.data.open[1]}, 前收盘价: {self.data.close[0]}, 阻力位: {self.resistance[0]}')
                self.break_bar = None
            # 3. 如果CSI小于等于阈值，开空单
            if strength <= -self.params.CSI_threshold:
                self.order = self.sell()
                self.entry_bar = len(self)
                print(f'{bt.num2date(self.data.datetime[1])}, 【开空单】: 价格: {self.data.open[1]}, 前收盘价: {self.data.close[0]}, 支撑位: {self.support[0]}')
                self.break_bar = None
            return

        # 突破阻力位逻辑
        if self.data.close[0] > self.resistance[0]:
            self.break_bar = len(self)
            print(f'{bt.num2date(self.data.datetime[0])} 突破阻力位，开始观察: 当前价格: {self.data.close[0]}, 阻力位: {self.resistance[0]}')
            return

        # 跌破支撑位逻辑
        if self.data.close[0] < self.support[0]:
            self.break_bar = len(self)
            print(f'{bt.num2date(self.data.datetime[0])} 跌破支撑位，开始观察: 当前价格: {self.data.close[0]}, 支撑位: {self.support[0]}')
            return

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None
            return

        # 跌破支撑位逻辑
        if self.data.close[0] < self.support[0]:
            self.break_bar = len(self)
            print(f'{bt.num2date(self.data.datetime[0])} 跌破支撑位，开始观察: 当前价格: {self.data.close[0]}, 支撑位: {self.support[0]}')
            return

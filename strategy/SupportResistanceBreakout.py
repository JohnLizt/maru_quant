import backtrader as bt
import pandas as pd

# 定义支撑位/阻力位突破策略
class SupportResistanceBreakout(bt.Strategy):
    params = (
        ('period', 20),  # 计算支撑位和阻力位的周期
        ('hold_days', 5),  # 持仓周期
        ('pullback_period', 2), # 回调周期
    )
    
    def __init__(self):
        # 定义支撑位和阻力位，subplot=False 画在主图
        self.support = bt.indicators.Lowest(self.data.low(-1), period=self.params.period, subplot=False)
        self.resistance = bt.indicators.Highest(self.data.high(-1), period=self.params.period, subplot=False)
        self.order = None
        self.entry_bar = None  # 记录开仓的bar号
        self.breakout_bar = None  # 记录突破阻力位的bar号
        self.breakdown_bar = None  # 记录跌破支撑位的bar号

    def next(self):
        # 如果有未完成订单，跳过
        if self.order:
            return

        # 平仓逻辑：持有多单或空单达到指定天数则平仓
        if self.position:
            if self.entry_bar is not None and (len(self) - self.entry_bar) >= self.params.hold_days:
                # 判断多空方向，正确计算利润
                if self.position.size > 0:
                    profit = self.data.close[0] - self.position.price
                else:
                    profit = self.position.price - self.data.close[0]
                print(f'{bt.num2date(self.data.datetime[0])}, 平仓:  当前价格: {self.data.close[0]}, 利润: {profit:.2f}')
                self.close()
                self.entry_bar = None
            return  # 平仓后本bar不再开新仓

        # 开多单逻辑
        if self.breakout_bar is not None:
            bars_since_breakout = len(self) - self.breakout_bar
            # 如果回调周期内价格跌破突破bar的open价格，取消等待
            breakout_open = self.data.open[self.breakout_bar - len(self)]
            if self.data.close[0] < breakout_open:
                print(f'{bt.num2date(self.data.datetime[0])}, 回调失败, 取消等待')
                self.breakout_bar = None
            # 回调周期结束且价格仍在阻力位上方，买入
            elif bars_since_breakout >= self.params.pullback_period:
                self.order = self.buy()
                self.entry_bar = len(self)
                print(f'{bt.num2date(self.data.datetime[1])}, 开多单: 当前价格: {self.data.open[1]}, 前日收盘价: {self.data.close[0]}, 阻力位: {self.resistance[0]}')
                self.breakout_bar = None
            return

        # 开空单逻辑
        if self.breakdown_bar is not None:
            bars_since_breakdown = len(self) - self.breakdown_bar
            # 如果回调周期内价格涨破跌破bar的open价格，取消等待
            breakdown_open = self.data.open[self.breakdown_bar - len(self)]
            if self.data.close[0] > breakdown_open:
                print(f'{bt.num2date(self.data.datetime[0])}, 回调失败, 取消等待')
                self.breakdown_bar = None
            # 回调周期结束且价格仍在支撑位下方，卖出开空
            elif bars_since_breakdown >= self.params.pullback_period:
                self.order = self.sell()
                self.entry_bar = len(self)
                print(f'{bt.num2date(self.data.datetime[1])}, 开空单: 当前价格: {self.data.open[1]}, 前日收盘价: {self.data.close[0]}, 支撑位: {self.support[0]}')
                self.breakdown_bar = None
            return

        # 突破阻力位逻辑
        if self.data.close[0] > self.resistance[0]:
            self.breakout_bar = len(self)
            print(f'{bt.num2date(self.data.datetime[0])}, 突破阻力位，等待回调确认: 当前价格: {self.data.close[0]}, 阻力位: {self.resistance[0]}')
            return

        # 跌破支撑位逻辑
        if self.data.close[0] < self.support[0]:
            self.breakdown_bar = len(self)
            print(f'{bt.num2date(self.data.datetime[0])}, 跌破支撑位，等待回调确认: 当前价格: {self.data.close[0]}, 支撑位: {self.support[0]}')
            return

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None

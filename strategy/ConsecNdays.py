import backtrader as bt

class ConsecNdays(bt.Strategy):
    params = (
        ('ndays', 4),  # 连续天数
    )

    def __init__(self):
        self.order = None
        self.is_closing = False  # 标记是否正在平仓

    def next(self):
        # 如果有未完成订单，跳过
        if self.order:
            return
        
        # 持有一天后平仓
        if self.position and not self.is_closing:
            self.order = self.close()
            self.is_closing = True
            return

        # 重置平仓标记
        if not self.position:
            self.is_closing = False

        n = self.p.ndays
        # 连续N天下跌
        if all(self.data.close[-i] < self.data.close[-i-1] for i in range(0, n)):
            self.order = self.buy()
            print(f"{bt.num2date(self.data.datetime[0])} 触发信号：连续{n}天下跌")
        # 连续N天上涨
        elif all(self.data.close[-i] > self.data.close[-i-1] for i in range(0, n)):
            self.order = self.sell()
            print(f"{bt.num2date(self.data.datetime[0])} 触发信号：连续{n}天上涨")

    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                if not self.is_closing:
                    print(f"{bt.num2date(order.executed.dt)} 开多单，价格: {order.executed.price}, 数量: {order.executed.size}")
            elif order.issell():
                if not self.is_closing:
                    print(f"{bt.num2date(order.executed.dt)} 开空单，价格: {order.executed.price}, 数量: {order.executed.size}")
            self.order = None
        elif order.status in [order.Canceled, order.Margin]:
            self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            print(f"{bt.num2date(self.data.datetime[0])} 平仓，利润: {trade.pnl:.2f}, 手续费: {trade.commission:.2f}")
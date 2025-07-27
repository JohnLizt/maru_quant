import backtrader as bt

class ShowData(bt.Strategy):
    
    def __init__(self):
        self.order = None

    def next(self):
        self.log(f"Current Close Price: {self.data.close[0]:.2f}, Date: {self.data.datetime.date(0)}")

    def notify_order(self, order):
        self.log("test")

    def notify_trade(self, trade):
        self.log("test")
    
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime[0]
        print('%s, %s' % (bt.num2date(dt).strftime('%Y-%m-%d %H:%M:%S'), txt))
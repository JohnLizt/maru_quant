import backtrader as bt

class CandleStrengthIndex(bt.Indicator):
    lines = ('csi',)
    params = (
        ('alpha', 0.5),
        ('beta', 0.3),
        ('gamma', 0.2),
    )

    def __init__(self):
        pass

    def next(self):
        open_ = self.data.open[0]
        high_ = self.data.high[0]
        low_ = self.data.low[0]
        close_ = self.data.close[0]
        if high_ == low_:
            self.lines.csi[0] = 0
            return
        entity = (close_ - open_) / (high_ - low_)
        close_pos = (2 * (close_ - low_) / (high_ - low_)) - 1
        shadow = 1 - (abs(high_ - close_) + abs(open_ - low_)) / (high_ - low_)
        strength = (
            self.p.alpha * entity +
            self.p.beta * close_pos +
            self.p.gamma * shadow
        )
        strength = max(min(strength, 1), -1)
        self.lines.csi[0] = strength
import backtrader as bt
import pandas as pd
from utils.logger import setup_strategy_logger

class SMA_V2(bt.Strategy):
    params = (
        ('ma_fast', 10),          # 快均线
        ('ma_slow', 20),          # 慢均线
        ('rsi_period', 14),       # RSI周期
        ('rsi_overbought', 70),   # RSI超买阈值
        ('rsi_oversold', 30),     # RSI超卖阈值
        ('atr_period', 14),       # ATR周期
        ('take_profit_atr', 2.5), # 止盈ATR倍数
        ('stop_loss_atr', 0.8),   # 止损ATR倍数
    )

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.entry_bar = None

        # 多重均线系统
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.ma_fast)
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.ma_slow)

        # 趋势过滤指标
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.params.rsi_period)
        self.atr = bt.indicators.ATR(self.datas[0], period=self.params.atr_period)
        self.macd = bt.indicators.MACDHisto(self.datas[0])
        
        # Bollinger Bands作为额外确认
        self.bbands = bt.indicators.BollingerBands(self.datas[0], period=20)

        self.logger = setup_strategy_logger(self, __name__, "INFO")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, ATR: %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     self.atr[0]))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.entry_bar = len(self)
            else:
                self.logger.info('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.info('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.logger.info('===== TRADE DONE, GROSS %.2f, NET %.2f, BARS HELD: %d =====' %
                 (trade.pnl, trade.pnlcomm, len(self) - self.entry_bar))

    def is_bullish_signal(self):
        """多重条件确认看涨信号"""
    
        # 2. 快慢均线确认趋势
        trend_confirm = self.sma_fast[0] > self.sma_slow[0]
        
        # 3. RSI不超买
        rsi_confirm = self.rsi[0] < self.params.rsi_overbought
        
        # 4. MACD确认动量
        macd_confirm = self.macd.macd[0] > self.macd.signal[0]
        
        # 5. 价格不在布林带上轨附近（避免超买区域）
        # bb_confirm = self.dataclose[0] < self.bbands.top[0] * 0.98

        # print which signal not satisfied
        if not trend_confirm:
            self.logger.info('Trend not confirmed: Fast SMA %.2f < Slow SMA %.2f' % (self.sma_fast[0], self.sma_slow[0]))
        if not rsi_confirm:
            self.logger.info('RSI not confirmed: %.2f > Overbought %.2f' % (self.rsi[0], self.params.rsi_overbought))
        if not macd_confirm:
            self.logger.info('MACD not confirmed: MACD %.4f < Signal %.4f' % (self.macd.macd[0], self.macd.signal[0]))

        return trend_confirm and rsi_confirm and macd_confirm

    def is_bearish_signal(self):
        """多重条件确认看跌信号"""
    
        # 2. 快慢均线确认趋势
        trend_confirm = self.sma_fast[0] < self.sma_slow[0]
        
        # 3. RSI不超卖
        rsi_confirm = self.rsi[0] > self.params.rsi_oversold
        
        # 4. MACD确认动量
        macd_confirm = self.macd.macd[0] < self.macd.signal[0]
        
        return trend_confirm and rsi_confirm and macd_confirm

    def check_exit_conditions(self):
        """检查退出条件"""
        if not self.position:
            return False
            
        # 动态止盈止损
        if self.position.size > 0:  # 多头持仓
            # ATR动态止损
            stop_loss_price = self.buyprice - self.atr[0] * self.params.stop_loss_atr
            take_profit_price = self.buyprice + self.atr[0] * self.params.take_profit_atr
            
            if (self.dataclose[0] <= stop_loss_price or 
                self.dataclose[0] >= take_profit_price or
                self.is_bearish_signal()):
                return True
                
        return False

    def next(self):
        # Check if an order is pending
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # 寻找买入信号
            if self.is_bullish_signal():
                self.logger.info('[↑↑SIG↑↑] BUY CREATE, %.2f, RSI: %.2f, MACD: %.4f' % 
                               (self.dataclose[0], self.rsi[0], self.macd.macd[0]))
                self.order = self.buy()

        else:
            # 检查退出条件
            if self.check_exit_conditions():
                self.logger.info('[↓↓SIG↓↓] SELL CREATE, %.2f, RSI: %.2f, P&L: %.2f' % 
                               (self.dataclose[0], self.rsi[0], 
                                (self.dataclose[0] - self.buyprice) * self.position.size))
                self.order = self.sell()
import backtrader as bt
import pandas as pd
from utils.logger import setup_strategy_logger

class BollingerBandsMeanReversionStrategy(bt.Strategy):
    params = (
        ('period', 20),           # Bollinger Bands period
        ('devfactor', 2.0),       # Standard deviation factor
        ('RSI_threshold', 30),    # RSI threshold for oversold condition
        ('stop_loss', 10),        # Stop loss absolute value
        ('take_profit', 10),      # Take profit absolute value
    )

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        # To keep track of pending orders and buy/sell prices
        self.order = None
        self.buyprice = None
        self.sellprice = None
        self.buycomm = None
        self.sellcomm = None

        # Add Bollinger Bands indicator
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.params.period,
            devfactor=self.params.devfactor
        )

        # Add RSI indicator for additional filtering
        self.rsi = bt.indicators.RSI(self.datas[0], period=14)

        # Setup logger
        self.logger = setup_strategy_logger(self, __name__, "INFO")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                
            elif order.issell():
                self.logger.info(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.sellprice = order.executed.price
                self.sellcomm = order.executed.comm

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.info('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.logger.info('===== TRADE DONE, GROSS %.2f, NET %.2f =====' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Not in position - look for entry signals
            
            # Mean reversion: Buy when price breaks below lower band AND RSI < 30 (oversold)
            if (self.dataclose[0] < self.bbands.bot[0] and self.rsi[0] < self.p.RSI_threshold):
                self.logger.info('[↑↑SIG↑↑] BUY CREATE (Below Lower Band + RSI<30), Price: %.2f, Lower Band: %.2f, RSI: %.2f' % 
                               (self.dataclose[0], self.bbands.bot[0], self.rsi[0]))
                self.order = self.buy()
                
            # Mean reversion: Sell when price breaks above upper band AND RSI > 70 (overbought)
            elif (self.dataclose[0] > self.bbands.top[0] and self.rsi[0] > 100 - self.p.RSI_threshold):
                self.logger.info('[↓↓SIG↓↓] SELL CREATE (Above Upper Band + RSI>70), Price: %.2f, Upper Band: %.2f, RSI: %.2f' % 
                               (self.dataclose[0], self.bbands.top[0], self.rsi[0]))
                self.order = self.sell()

        else:
            # We are in position - check for exit signals
            
            if self.position.size > 0:  # Long position
                # Calculate stop loss and take profit levels using absolute values
                stop_loss_price = self.buyprice - self.params.stop_loss
                take_profit_price = self.buyprice + self.params.take_profit
                
                # Exit conditions for long position
                if (self.dataclose[0] <= stop_loss_price or 
                    self.dataclose[0] >= take_profit_price or
                    self.dataclose[0] > self.bbands.mid[0]):  # Price back to middle band
                    
                    exit_reason = ""
                    if self.dataclose[0] <= stop_loss_price:
                        exit_reason = "Stop Loss"
                    elif self.dataclose[0] >= take_profit_price:
                        exit_reason = "Take Profit"
                    else:
                        exit_reason = "Mean Reversion to Mid"
                        
                    self.logger.info('SELL CREATE (%s), Price: %.2f' % (exit_reason, self.dataclose[0]))
                    self.order = self.sell()

            elif self.position.size < 0:  # Short position
                # Calculate stop loss and take profit levels using absolute values
                stop_loss_price = self.sellprice + self.params.stop_loss
                take_profit_price = self.sellprice - self.params.take_profit
                
                # Exit conditions for short position
                if (self.dataclose[0] >= stop_loss_price or 
                    self.dataclose[0] <= take_profit_price or
                    self.dataclose[0] < self.bbands.mid[0]):  # Price back to middle band
                    
                    exit_reason = ""
                    if self.dataclose[0] >= stop_loss_price:
                        exit_reason = "Stop Loss"
                    elif self.dataclose[0] <= take_profit_price:
                        exit_reason = "Take Profit"
                    else:
                        exit_reason = "Mean Reversion to Mid"
                        
                    self.logger.info('BUY CREATE (%s), Price: %.2f' % (exit_reason, self.dataclose[0]))
                    self.order = self.buy()
            self.logger.info(f'HOLD: Price: {self.dataclose[0]:.2f}, Position: {self.position.size}, Cash: {self.broker.getcash():.2f}')

    def stop(self):
        self.logger.info('Ending Value %.2f' % self.broker.getvalue())

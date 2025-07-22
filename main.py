import backtrader as bt
import pandas as pd
import warnings
import os

from strategy.Breakout import Breakout
from strategy.ConsecNdays import ConsecNdays
from utils.dataloader import load_data
from utils.config_loader import load_config
from strategy.SMAStrategy import SMAStrategy
from analyzer.WinLossRatioAnalyzer import WinLossRatioAnalyzer

# config
config = load_config().get("backtest_config", {})

dataFile = config.get("file")
start_date = config.get("start_date")
end_date = config.get("end_date")
cash = config.get("cash", 100000.0)  # Default starting cash
commission = config.get("commission", 0.00015)  # Default commission rate
sizer = config.get("sizer", "FixedSize")  # Default sizer type
fixed_size_stake = config.get("fixed_size_stake", 1)  # Default fixed size of shares


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    
    # load data
    data_feed = load_data(dataFile, start_date, end_date)
    cerebro.adddata(data_feed)

    # Add strategy
    cerebro.addstrategy(
        Breakout,
        window=12,
        threshold=0.001
    )
    # cerebro.addstrategy(SMAStrategy)

    # Set broker parameters
    cerebro.broker.setcash(cash)  # Starting cash
    cerebro.broker.setcommission(commission)  # 0.015% commission
    cerebro.addsizer(bt.sizers.FixedSize, stake=fixed_size_stake)  # Fixed size of shares

    # add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(WinLossRatioAnalyzer, _name='winloss')

    # Run backtest
    result = cerebro.run()

    # Plot results、
    print('----------------------backtesting results----------------------')
    print('sharpe_ratio:', result[0].analyzers.sharpe_ratio.get_analysis())
    print('drawdown:', result[0].analyzers.drawdown.get_analysis()['max']['drawdown']) 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Win/Loss/Profit-Loss Ratio:', result[0].analyzers.winloss.get_analysis())
    
    end_value = cerebro.broker.getvalue()
    profit_rate = (end_value - cash) / cash
    print('Final Profit Rate: {:.2%}'.format(profit_rate))
    warnings.filterwarnings("ignore", category=UserWarning, module="backtrader.plot.locator")
    cerebro.plot(
        style='candlestick',      # 设置显示为蜡烛图
        bgcolor='white',          # 设置背景色
        tight_layout=True,        # 紧凑布局
        # volume=False              # 不画成交量
    )


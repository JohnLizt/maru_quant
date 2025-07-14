import backtrader as bt
import pandas as pd
import warnings
import os

from dataloader import load_data
from downloader.config_loader import load_config
from strategy.SMAStrategy import SMAStrategy
from strategy.SupportResistanceBreakout import SupportResistanceBreakout

# config
config = load_config().get("backtest_config", {})

dataFile = config.get("file")
start_date = config.get("start_date")
end_date = config.get("end_date")
cash = config.get("cash", 100000.0)  # Default starting cash
commission = config.get("commission", 0.0006)  # Default commission rate
sizer = config.get("sizer", "FixedSize")  # Default sizer type
fixed_size_stake = config.get("fixed_size_stake", 1)  # Default fixed size of shares


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    
    # load data
    data_feed = load_data(dataFile, start_date, end_date)
    cerebro.adddata(data_feed)

    # Add strategy
    cerebro.addstrategy(SupportResistanceBreakout, period=20, hold_days=5, pullback_period=2)  # Use SupportResistanceBreakout strategy

    # Set broker parameters
    cerebro.broker.setcash(cash)  # Starting cash
    cerebro.broker.setcommission(commission)  # 0.1% commission
    cerebro.addsizer(bt.sizers.FixedSize, stake=fixed_size_stake)  # Fixed size of shares

    # add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # Run backtest
    result = cerebro.run()

    # Plot results
    print('sharpe_ratio:', result[0].analyzers.sharpe_ratio.get_analysis())
    print('drawdown:', result[0].analyzers.drawdown.get_analysis()['max']['drawdown']) 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    end_value = cerebro.broker.getvalue()
    profit_rate = (end_value - cash) / cash
    print('Final Profit Rate: {:.2%}'.format(profit_rate))
    warnings.filterwarnings("ignore", category=UserWarning, module="backtrader.plot.locator")
    cerebro.plot(
        style='candlestick',      # 设置显示为蜡烛图
        bgcolor='white',          # 设置背景色
        tight_layout=True,        # 紧凑布局
        plotdist=0,               # 让买卖点贴近K线
        # volume=False              # 不画成交量
    )


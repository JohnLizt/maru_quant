from pprint import pprint
import backtrader as bt
import pandas as pd
import warnings
import os

from strategy.breakout.SimpleBreakout import SimpleBreakout
from strategy.ConsecNdays import ConsecNdays
from utils.dataloader import load_data
from utils.config_loader import load_config
from strategy.SMAStrategy import SMAStrategy
from analyzer.WinLossRatioAnalyzer import WinLossRatioAnalyzer
from utils.optimizer import GridSearchOptimizer
from trade.CommissionInfo import comm_ibkr_XAUUSD

# config
config = load_config()
backtest_config = config.get("backtest_config", {})
broker_config = config.get("broker_config", {})

dataFile = backtest_config.get("file")
start_date = backtest_config.get("start_date")
end_date = backtest_config.get("end_date")
sizer = backtest_config.get("sizer", "percents")  # Default sizer type
size_percent = backtest_config.get("size_percent", 100)  # Default size percent
fixed_size_stake = backtest_config.get("fixed_size_stake", 1)  # Default fixed size of shares
OPTIMIZE_MODE = backtest_config.get("optimize_mode", False)  # 设置为True启用优化模式

# broker config
tick_type = broker_config.get("tick_type", "stock")
cash = broker_config.get("cash", 100000.0)  # Default starting cash
commission = broker_config.get("commission_rate", 0.00015)  # Default commission rate
spread = broker_config.get("spread", 0.16)  # Default spread

def run_optimization():
    """运行参数优化"""
    print("开始参数优化...")
    
    # 加载数据
    data_feed = load_data(dataFile, start_date, end_date)
    
    # 创建优化器
    optimizer = GridSearchOptimizer(
        strategy_class=SimpleBreakout,
        data_feed=data_feed,
        cash=cash,
        commission=commission,
        stake=fixed_size_stake,
        sizer_type=sizer,
        size_percent=size_percent,
        tick_type=tick_type
    )
    
    # 定义参数网格
    param_grid = {
        'window': [8, 12, 16],
        'threshold': [0.001, 0.002, 0.005],
        'max_hold_bars': [6, 15, 24],
        'take_profit': [0.004, 0.006, 0.008],
        'stop_loss': [0.002, 0.003, 0.005],
        'sma_period': [10, 20]
    }
    
    # 执行优化
    results_df = optimizer.optimize(param_grid)
    
    # 显示结果
    print("\n=== 优化结果 (前10名) ===")
    print(results_df.head(10).to_string(index=False))
    
    # 获取最佳参数
    best_params = optimizer.get_best_params('total_return')  # 使用total_return而不是sharpe_ratio
    print(f"\n=== 最佳参数组合 (按总收益率排序) ===")
    for param, value in best_params.items():
        print(f"{param}: {value}")
    
    # 保存结果
    results_df.to_csv('utils/optimization_results.csv', index=False)
    print("\n优化结果已保存到 optimization_results.csv")

def run_backtest():
    """运行常规回测"""
    cerebro = bt.Cerebro()
    
    # load data
    data_feed = load_data(dataFile, start_date, end_date)
    cerebro.adddata(data_feed)

    # Add strategy
    # cerebro.addstrategy(SMAStrategy) # baseline: SMAStrategy
    cerebro.addstrategy(
        SimpleBreakout
        )

    # Set broker parameters
    cerebro.broker.setcash(cash)  # Starting cash
    
    # Set commission based on tick type
    if tick_type == "futures":
        cerebro.broker.addcommissioninfo(comm_ibkr_XAUUSD)
        print("=== CommissionInfo 配置 ===")
        print(f"佣金: ${comm_ibkr_XAUUSD.p.commission}")
        print(f"合约乘数: {comm_ibkr_XAUUSD.p.mult}")
        print(f"期货类型: {not comm_ibkr_XAUUSD.p.stocklike}")
        print(f"资金 ${cash}")
    else:
        cerebro.broker.setcommission(commission)  # Default commission for stocks/forex
    
    if sizer == "fixed":
        cerebro.addsizer(bt.sizers.FixedSize, stake=fixed_size_stake)  # Fixed size of shares
    elif sizer == "percents":
        cerebro.addsizer(bt.sizers.PercentSizerInt, percents=size_percent)  # Default to 10% of cash

    # add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(WinLossRatioAnalyzer, _name='winloss')

    # Run backtest
    result = cerebro.run()

    # 显示结果
    print('----------------------backtesting results----------------------')
    # print('sharpe_ratio:', result[0].analyzers.sharpe_ratio.get_analysis())
    print('drawdown:', result[0].analyzers.drawdown.get_analysis()['max']['drawdown']) 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Win/Loss/Profit-Loss Ratio:', result[0].analyzers.winloss.get_analysis())
    
    end_value = cerebro.broker.getvalue()
    profit_rate = (end_value - cash) / cash
    print('Final Profit Rate: {:.2%}'.format(profit_rate))
    warnings.filterwarnings("ignore", category=UserWarning, module="backtrader.plot.locator")
    cerebro.plot(
        style='candlestick',
        bgcolor='white',
        tight_layout=True,
    )

if __name__ == "__main__":
    if OPTIMIZE_MODE:
        run_optimization()
    else:
        run_backtest()


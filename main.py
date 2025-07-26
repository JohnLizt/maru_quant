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

# config
config = load_config().get("backtest_config", {})

dataFile = config.get("file")
start_date = config.get("start_date")
end_date = config.get("end_date")
cash = config.get("cash", 100000.0)  # Default starting cash
commission = config.get("commission", 0.00015)  # Default commission rate
sizer = config.get("sizer", "percents")  # Default sizer type
size_percent = config.get("size_percent", 100)  # Default size percent
fixed_size_stake = config.get("fixed_size_stake", 1)  # Default fixed size of shares
OPTIMIZE_MODE = config.get("optimize_mode", False)  # 设置为True启用优化模式

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
        size_percent=size_percent
    )
    
    # 定义参数网格
    param_grid = {
        'window': [5, 8, 12, 16],
        'threshold': [0.001, 0.002, 0.005],
        'take_profit': [0.003, 0.005, 0.008],
        'stop_loss': [0.002, 0.0025, 0.003],
        'sma_period': [8, 10, 12, 20]
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
    cerebro.addstrategy(SimpleBreakout)

    # Set broker parameters
    cerebro.broker.setcash(cash)  # Starting cash
    cerebro.broker.setcommission(commission)  # 0.015% commission
    if sizer == "fixed":
        cerebro.addsizer(bt.sizers.FixedSize, stake=fixed_size_stake)  # Fixed size of shares
    elif sizer == "percents":
        cerebro.addsizer(bt.sizers.PercentSizerInt, percents=size_percent)  # Default to 10% of cash

    # add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(WinLossRatioAnalyzer, _name='winloss')

    # Run backtest
    result = cerebro.run()

    # 显示结果
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
        style='candlestick',
        bgcolor='white',
        tight_layout=True,
    )

if __name__ == "__main__":
    if OPTIMIZE_MODE:
        run_optimization()
    else:
        run_backtest()


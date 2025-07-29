from pprint import pprint
import backtrader as bt
import pandas as pd
import warnings
import os
import re

from analyzer.robustsharpe_30min import RobustSharpe_30min
from analyzer.sharperatio_30min import SharpeRatio_30min
from strategy.breakout.SimpleBreakout import SimpleBreakout
from strategy.showdata import ShowData
from utils.dataloader import load_data
from utils.config_loader import load_config
from strategy.SMAStrategy import SMAStrategy
from analyzer.WinLossRatioAnalyzer import WinLossRatioAnalyzer
from utils.fileoperator import extract_dates_from_filename
from utils.optimizer import GridSearchOptimizer
from trade.CommissionInfo import comm_ibkr_XAUUSD
from utils.walkforward import WalkForwardAnalyzer
from utils.logger import setup_logger, get_logger

# config
config = load_config()
backtest_config = config.get("backtest_config", {})
broker_config = config.get("broker_config", {})

# backtest config
basic_config = backtest_config.get("basic", {})
sizer_config = backtest_config.get("sizer", {})
optimize_config = backtest_config.get("optimize", {})
validation_config = backtest_config.get("validation", {})

dataFile = basic_config.get("file")
start_date = basic_config.get("start_date")
end_date = basic_config.get("end_date")
sizer = sizer_config.get("sizer", "percents")  # Default sizer type
size_percent = sizer_config.get("size_percent", 100)  # Default size percent
fixed_size_stake = sizer_config.get("fixed_size_stake", 1)  # Default fixed size of shares
OPTIMIZE_MODE = optimize_config.get("optimize_mode", False)  # 设置为True启用优化模式
WALK_FORWARD_MODE = validation_config.get("walk_forward_mode", False)  # Walk-Forward模式

# broker config
tick_type = broker_config.get("tick_type", "stock")
multiplier = broker_config.get("multiplier", 1)
cash = broker_config.get("cash", 100000.0)  # Default starting cash
leverage = broker_config.get("leverage", 1.0)
fixed_commission = broker_config.get("fixed_commission", False)
commission = broker_config.get("commission", 0.00015)  # Default commission rate
spread = broker_config.get("spread", 0.16)  # Default spread

# parse start-end date from filename
fname_start_date, fname_end_date = extract_dates_from_filename(dataFile)

# Initialize logger
logger_config = config.get("logger_config", {})
log_level = logger_config.get("log_level", "INFO")
log_to_console = logger_config.get("log_to_console", True)
log_to_file = logger_config.get("log_to_file", True)
logger = setup_logger("main", log_level, log_to_file)


def run_backtest():
    """运行常规回测"""
    logger.info("start backtesting...")
    cerebro = bt.Cerebro()
    
    # load data
    data_feed = load_data(dataFile, start_date, end_date)
    cerebro.adddata(data_feed)

    # Add strategy
    # cerebro.addstrategy(ShowData)
    # cerebro.addstrategy(SMAStrategy) # baseline
    cerebro.addstrategy(
        SimpleBreakout,
        window=16,
        threshold=0.001,
        max_hold_bars=24,
        take_profit=35,
        stop_loss=25,
        sma_period=20
    )

    # Set broker parameters
    cerebro.broker.setcash(cash)  # Starting cash
    
    # Set commission based on tick type
    if tick_type == "CFD":
        cerebro.broker.addcommissioninfo(comm_ibkr_XAUUSD)
    else:
        cerebro.broker.setcommission(commission)  # Default commission for stocks/forex
    
    if sizer == "fixed":
        cerebro.addsizer(bt.sizers.FixedSize, stake=fixed_size_stake)  # Fixed size of shares
    elif sizer == "percents":
        cerebro.addsizer(bt.sizers.PercentSizerInt, percents=size_percent)  # Default to 10% of cash

    # add analyzers
    cerebro.addanalyzer(SharpeRatio_30min, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(WinLossRatioAnalyzer, _name='winloss')

    # Run backtest
    result = cerebro.run()

    # 显示结果
    logger.info('================= backtesting results ======================')
    logger.info(f"from: {fname_start_date} to {fname_end_date}")
    logger.info('sharpe_ratio: %s', result[0].analyzers.sharpe_ratio.get_analysis())
    logger.info('max drawdown: %.4f', result[0].analyzers.drawdown.get_analysis()['max']['drawdown'])
    logger.info('Win/Loss/PL Ratio: %s', result[0].analyzers.winloss.get_analysis())
    logger.info('Final Portfolio Value: %.2f', cerebro.broker.getvalue())
    
    end_value = cerebro.broker.getvalue()
    profit_rate = (end_value - cash) / cash
    logger.info('Final Profit Rate: {:.2%}'.format(profit_rate))
    warnings.filterwarnings("ignore", category=UserWarning, module="backtrader.plot.locator")
    cerebro.plot(
        style='candlestick',
        bgcolor='white',
        tight_layout=True,
    )

def run_optimization():
    """运行参数优化"""
    logger.info("开始参数优化...")
    
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
        'window': [6, 12, 16, 20],
        'threshold': [0.001],
        'max_hold_bars': [24],
        'take_profit': [20, 25, 30, 35, 40, 45],
        'stop_loss': [10, 15, 20, 25, 30],
        'sma_period': [20]
    }
    
    # 执行优化
    results_df = optimizer.optimize(param_grid)
    
    # 显示结果
    logger.info("=== 优化结果 (前10名) ===")
    logger.info(results_df.head(10).to_string(index=False))
    
    # 获取最佳参数
    best_params = optimizer.get_best_params('sharpe_ratio')
    logger.info("=== 最佳参数组合 (按夏普比率排序) ===")
    for param, value in best_params.items():
        logger.info(f"{param}: {value}")
    
    # 保存结果
    results_df.to_csv('utils/optimize_result/optimization_results.csv', index=False)
    logger.info("优化结果已保存到 utils/optimize_result/optimization_results.csv")


def run_walk_forward():
    """运行Walk-Forward Analysis"""
    logger.info("运行Walk-Forward Analysis...")
    
    # 创建分析器
    wf_analyzer = WalkForwardAnalyzer(
        strategy_class=SMAStrategy,
        data_file=dataFile,
        start_date=start_date,
        end_date=end_date,
        cash=cash,
        commission=commission,
        stake=fixed_size_stake,
        sizer_type=sizer,
        size_percent=size_percent,
        tick_type=tick_type
    )
    
    # 定义参数网格
    # param_grid = {
    #     'window': [16],
    #     'threshold': [0.001],
    #     'take_profit': [15, 25, 35],
    #     'stop_loss': [5, 15, 25],
    #     'sma_period': [20]
    # }
    param_grid = {
        'maperiod': [20]
    }
    
    # 执行Walk-Forward分析
    wf_analyzer.run_walk_forward_analysis(
        param_grid=param_grid,
        train_quarters=validation_config.get("train_quarters", 2),  # Use config value
        test_quarters=validation_config.get("test_quarters", 1)     # Use config value
    )
    
    # 显示汇总统计
    summary_stats = wf_analyzer.get_summary_statistics()
    logger.info("=== Walk-Forward Analysis 汇总统计 ===")
    for key, value in summary_stats.items():
        if isinstance(value, float):
            logger.info(f"{key}: {value:.4f}")
        else:
            logger.info(f"{key}: {value}")
    
    # 保存结果
    wf_analyzer.save_results()
    
    return wf_analyzer

if __name__ == "__main__":
    if WALK_FORWARD_MODE:
        run_walk_forward()
    elif OPTIMIZE_MODE:
        run_optimization()
    else:
        run_backtest()


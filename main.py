from strategy.breakout.SimpleBreakout import SimpleBreakout
from utils.dataloader import load_data
from strategy.SMAStrategy import SMAStrategy
from utils.fileoperator import extract_dates_from_filename
from utils.optimizer import GridSearchOptimizer
from utils.walkforward import WalkForwardAnalyzer
from utils.logger import setup_logger
from utils.backtest_runner import BacktestRunner
from utils.config_manager import config_manager

# 从配置管理器获取配置
dataFile = config_manager.data_file
start_date = config_manager.start_date
end_date = config_manager.end_date

# parse start-end date from filename
fname_start_date, fname_end_date = extract_dates_from_filename(dataFile)

# initialize logger
if (config_manager.walk_forward_mode or config_manager.optimize_mode):
    logger = setup_logger("main", config_manager.log_level, True) # 固定输出日志到文件
else:
    logger = setup_logger("main", config_manager.log_level, config_manager.log_to_file)


def run_backtest():
    """运行常规回测"""
    logger.info("========== start backtesting... ==========")
    
    # 直接从配置创建回测运行器
    runner = BacktestRunner.from_config()
    
    # load data
    data_feed = load_data(dataFile, start_date, end_date)
    
    # 策略参数
    strategy_params = {
        'window': 16,
        'threshold': 0.001,
        'max_hold_bars': 24,
        'take_profit': 35,
        'stop_loss': 25,
        'sma_period': 20
    }
    
    # 运行回测
    result = runner.run(SimpleBreakout, data_feed, strategy_params)
    
    if result:
        # 显示结果
        logger.info('================= backtesting results ======================')
        logger.info(f"From: {fname_start_date} To {fname_end_date}")
        logger.info('Sharpe Ratio: %.4f', result['sharpe_ratio'])
        logger.info('Max Drawdown: %.2f%%', result['max_drawdown'])
        logger.info('Profit Rate: {:.2%}'.format(result['total_return']))
        logger.info('Total_Trade: %d', result['total_trade'])
        logger.info('Win Rate: %.2f%%', result['win_rate'])
        logger.info('Avg Win: %.4f', result['avg_win'])
        logger.info('Avg Loss: %.4f', result['avg_loss'])
        logger.info('P/L Ratio: %.4f', result['P/L_ratio'])
        logger.info('Final Portfolio Value: %.2f', result['final_value'])
    else:
        logger.error("回测失败")

def run_optimization():
    """运行参数优化"""
    logger.info("开始参数优化...")
    
    # 加载数据
    data_feed = load_data(dataFile, start_date, end_date)
    
    # 创建优化器 - 直接使用配置管理器的参数
    optimizer = GridSearchOptimizer(
        strategy_class=SimpleBreakout,
        data_feed=data_feed,
        **config_manager.get_backtest_params()
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
    
    # 创建分析器 - 直接使用配置管理器的参数
    wf_analyzer = WalkForwardAnalyzer(
        strategy_class=SMAStrategy,
        data_file=dataFile,
        start_date=start_date,
        end_date=end_date,
        **config_manager.get_backtest_params()
    )
    
    # 定义参数网格
    param_grid = {
        # 'window': [16],
        # 'threshold': [0.001],
        # 'take_profit': [35],
        # 'stop_loss': [25],
        # 'sma_period': [15],
        # 'max_hold_bars': [24]
    }
    
    # 执行Walk-Forward分析
    wf_analyzer.run_walk_forward_analysis(
        param_grid=param_grid,
        train_quarters=config_manager.validation_config.get("train_quarters", 4),
        test_quarters=config_manager.validation_config.get("test_quarters", 2)
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
    if config_manager.walk_forward_mode:
        run_walk_forward()
    elif config_manager.optimize_mode:
        run_optimization()
    else:
        run_backtest()

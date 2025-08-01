import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import warnings
import numpy as np

from maru_quant.utils import config_manager
from maru_quant.utils.optimizer import GridSearchOptimizer
from maru_quant.utils.dataloader import load_data
from maru_quant.utils import BacktestRunner
from maru_quant.utils.logger import get_logger, setup_logger

class WalkForwardAnalyzer:
    def __init__(self, strategy_class, data_file, start_date, end_date, 
                 cash=100000, commission=0.00015, stake=1, sizer_type="percents", 
                 size_percent=100, tick_type="stock"):
        """
        Walk-Forward Analysis分析器
        
        Args:
            strategy_class: 策略类
            data_file: 数据文件路径
            start_date: 开始日期 (空字符串或None时使用数据集全部数据)
            end_date: 结束日期 (空字符串或None时使用数据集全部数据)
            其他参数: 回测配置参数
        """
        self.strategy_class = strategy_class
        self.data_file = data_file
        self.logger = setup_logger("walk forward analyzer", config_manager.log_level, True) # 固定输出到文件
        
        # 打印当前使用的策略名称
        self.strategy_name = strategy_class.__name__ if hasattr(strategy_class, '__name__') else str(strategy_class)
        self.logger.info(f"当前使用的策略: {self.strategy_name}")
        
        # 创建BacktestRunner实例
        self.backtest_runner = BacktestRunner(
            cash=cash,
            commission=commission,
            stake=stake,
            sizer_type=sizer_type,
            size_percent=size_percent,
            tick_type=tick_type
        )
        
        # 处理空的start_date和end_date - 只加载一次数据
        need_load_data = (not start_date or start_date == "") or (not end_date or end_date == "")
        if need_load_data:
            self.logger.info("检测到空的日期参数，正在加载数据获取日期范围...")
            full_data = load_data(data_file, None, None)
            data_index = full_data._dataname.index
            
            if not start_date or start_date == "":
                self.start_date = pd.to_datetime(data_index[0])
                self.logger.info(f"使用数据集开始日期: {self.start_date.strftime('%Y-%m-%d')}")
            else:
                self.start_date = pd.to_datetime(start_date)
                
            if not end_date or end_date == "":
                self.end_date = pd.to_datetime(data_index[-1])
                self.logger.info(f"使用数据集结束日期: {self.end_date.strftime('%Y-%m-%d')}")
            else:
                self.end_date = pd.to_datetime(end_date)
        else:
            self.start_date = pd.to_datetime(start_date)
            self.end_date = pd.to_datetime(end_date)
            
        self.cash = cash
        self.commission = commission
        self.stake = stake
        self.sizer_type = sizer_type
        self.size_percent = size_percent
        self.tick_type = tick_type
        
        # 存储结果
        self.train_results = []  # 训练期优化结果
        self.test_results = []   # 测试期验证结果
        self.walk_forward_results = []  # 汇总结果
        
    def generate_quarterly_windows(self, train_quarters=8, test_quarters=1):
        """
        生成季度窗口
        
        Args:
            train_quarters: 训练期季度数 (默认8个季度=2年)
            test_quarters: 测试期季度数 (默认1个季度)
            
        Returns:
            List of (train_start, train_end, test_start, test_end) tuples
        """
        windows = []
        current_start = self.start_date
        
        while True:
            # 计算训练期结束时间
            train_end = current_start + pd.DateOffset(months=3*train_quarters)
            
            # 计算测试期结束时间
            test_end = train_end + pd.DateOffset(months=3*test_quarters)
            
            # 如果测试期超出总数据范围，停止
            if test_end > self.end_date:
                break
                
            windows.append((
                current_start.strftime('%Y-%m-%d'),
                train_end.strftime('%Y-%m-%d'), 
                train_end.strftime('%Y-%m-%d'),
                test_end.strftime('%Y-%m-%d')
            ))
            
            # 向前滚动一个季度
            current_start = current_start + pd.DateOffset(months=3)
            
        return windows
    
    def run_walk_forward_analysis(self, param_grid: Dict[str, List[Any]], 
                                 train_quarters=4, test_quarters=2):
        """
        执行Walk-Forward Analysis
        
        Args:
            param_grid: 参数网格
            train_quarters: 训练期季度数
            test_quarters: 测试期季度数
        """
        self.logger.info(f"开始Walk-Forward Analysis...")
        self.logger.info(f"训练期: {train_quarters}个季度, 测试期: {test_quarters}个季度")
        
        # 生成时间窗口
        windows = self.generate_quarterly_windows(train_quarters, test_quarters)
        self.logger.info(f"总共生成 {len(windows)} 个窗口")
        
        for i, (train_start, train_end, test_start, test_end) in enumerate(windows):
            self.logger.info(f"=== 窗口 {i+1}/{len(windows)} ===")
            self.logger.info(f"训练期: {train_start} 至 {train_end}")
            self.logger.info(f"测试期: {test_start} 至 {test_end}")
            
            # 1. 训练期优化
            self.logger.info("正在训练期优化参数...")
            train_data = load_data(self.data_file, train_start, train_end)
            
            optimizer = GridSearchOptimizer(
                strategy_class=self.strategy_class,
                data_feed=train_data,
                cash=self.cash,
                commission=self.commission,
                stake=self.stake,
                sizer_type=self.sizer_type,
                size_percent=self.size_percent,
                tick_type=self.tick_type
            )
            
            # 执行参数优化
            train_results_df = optimizer.optimize(param_grid)
            
            if train_results_df.empty:
                self.logger.warning("训练期优化失败，跳过此窗口")
                continue
                
            # 获取最佳参数
            best_params = optimizer.get_best_params('sharpe_ratio')
            self.logger.info(f"最佳参数: {best_params}")
            
            # 记录训练结果
            train_result = {
                'window_idx': i+1,
                'train_start': train_start,
                'train_end': train_end,
                'best_params': best_params,
                'train_performance': train_results_df.iloc[0].to_dict()
            }
            self.train_results.append(train_result)
            
            # 2. 测试期验证
            self.logger.info("正在测试期验证...")
            test_result = self._run_test_period(best_params, test_start, test_end)
            
            if test_result:
                test_result.update({
                    'window_idx': i+1,
                    'test_start': test_start,
                    'test_end': test_end,
                    'best_params': best_params
                })
                self.test_results.append(test_result)
                
                # 汇总结果
                train_sharpe = train_result['train_performance']['sharpe_ratio']
                summary = {
                    'window_idx': i+1,
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end,
                    'efficiency': test_result['sharpe_ratio'] / train_sharpe if train_sharpe != 0 else 0,
                    'train_sharpe': train_sharpe,
                    'test_sharpe': test_result['sharpe_ratio'],
                    'train_return': train_result['train_performance']['total_return'],
                    'test_return': test_result['total_return'],
                    'train_max_dd': train_result['train_performance']['max_drawdown'],
                    'test_max_dd': test_result['max_drawdown'],
                    'train_win_rate': train_result['train_performance']['win_rate'],
                    'test_win_rate': test_result['win_rate'],
                    'train_PL_ratio': train_result['train_performance']['P/L_ratio'],
                    'test_PL_ratio': test_result['P/L_ratio']
                }
                self.walk_forward_results.append(summary)
                self.logger.info(f"=== 测试期验证结果 === ")
                self.logger.info(f"夏普比率: {test_result['sharpe_ratio']:.2f}")
                self.logger.info(f"最大回撤: {test_result['max_drawdown']:.2f}%")
                self.logger.info(f"收益率: {test_result['total_return']:.2%}")
                self.logger.info(f"胜率: {test_result['win_rate']:.2f}%")
                self.logger.info(f"盈亏比: {test_result['P/L_ratio']:.2f}")
                self.logger.info(f"Walk forward 效率: {summary['efficiency']:.2f}")
            else:
                self.logger.warning("测试期验证失败")

    def _run_test_period(self, params: Dict[str, Any], test_start: str, test_end: str):
        """运行测试期回测"""
        try:
            # 加载测试期数据
            test_data = load_data(self.data_file, test_start, test_end)
            
            # 使用BacktestRunner
            result = self.backtest_runner.run(
                strategy_class=self.strategy_class,
                data_feed=test_data,
                params=params
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"测试期回测失败: {str(e)}")
            return None
    
    def get_summary_statistics(self):
        """获取汇总统计"""
        if not self.walk_forward_results:
            return {}
            
        df = pd.DataFrame(self.walk_forward_results)

        # 计算权重：给近期数据更大权重（平方根递增）
        num_windows = len(df)
        weights = [(i + 1) ** 0.5 for i in range(num_windows)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # 使用加权平均计算关键指标
        avg_test_sharpe = sum(df['test_sharpe'].iloc[i] * normalized_weights[i] for i in range(num_windows))
        avg_test_max_dd = sum(df['test_max_dd'].iloc[i] * normalized_weights[i] for i in range(num_windows))
        avg_test_return = sum(df['test_return'].iloc[i] * normalized_weights[i] for i in range(num_windows))
        avg_test_win_rate = sum(df['test_win_rate'].iloc[i] * normalized_weights[i] for i in range(num_windows))
        avg_test_PL_ratio = sum(df['test_PL_ratio'].iloc[i] * normalized_weights[i] for i in range(num_windows))
        avg_efficiency = sum(df['efficiency'].iloc[i] * normalized_weights[i] for i in range(num_windows))
        
        return {
            'Strategy': self.strategy_name,
            'Total Windows': len(df),
            'Avg Test Sharpe': avg_test_sharpe,
            'Avg Test MaxDd': avg_test_max_dd,
            'WFE': avg_efficiency,
            'Std WFE': df['efficiency'].std(),
            'Avg Test WinRate': avg_test_win_rate,
            'Avg Test PL Ratio': avg_test_PL_ratio,
            'Avg Test Return': avg_test_return,
            'Std Test Return': df['test_return'].std(),
            'Best Test Return': df['test_return'].max(),
            'Worst Test Return': df['test_return'].min(),
            'Period Win Rate': (df['test_return'] > 0).mean(),
            'Consistency Score': df['test_return'].mean() / df['test_return'].std() if df['test_return'].std() > 0 else 0,
        }
    
    def save_results(self, output_dir='results/walk_forward_results'):
        """保存结果"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存详细结果
        if self.walk_forward_results:
            df_summary = pd.DataFrame(self.walk_forward_results)
            df_summary.to_csv(f'{output_dir}/walk_forward_summary.csv', index=False)
            
        if self.train_results:
            # 保存训练结果（需要特殊处理嵌套字典）
            self.logger.info("正在保存训练期优化结果...")
            train_flat = []
            for result in self.train_results:
                flat_result = {
                    'window_idx': result['window_idx'],
                    'train_start': result['train_start'],
                    'train_end': result['train_end']
                }
                flat_result.update(result['best_params'])
                flat_result.update(result['train_performance'])
                self.logger.info(f"{flat_result}")
                train_flat.append(flat_result)

            df_train = pd.DataFrame(train_flat)
            df_train.to_csv(f'{output_dir}/train_results.csv', index=False)
            
        if self.test_results:
            # 保存测试结果
            test_flat = []
            for result in self.test_results:
                flat_result = {k: v for k, v in result.items() if k != 'winloss_stats'}
                if 'winloss_stats' in result:
                    flat_result.update(result['winloss_stats'])
                test_flat.append(flat_result)
            
            df_test = pd.DataFrame(test_flat)
            df_test.to_csv(f'{output_dir}/test_results.csv', index=False)
        
        self.logger.info(f"结果已保存到 {output_dir}")
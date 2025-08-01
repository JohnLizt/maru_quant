import backtrader as bt
import itertools
import pandas as pd
from typing import Dict, List, Any, Tuple
from maru_quant.utils import config_manager
from maru_quant.utils import BacktestRunner
from maru_quant.utils.logger import get_logger, setup_logger

class GridSearchOptimizer:
    def __init__(self, strategy_class, data_feed, cash=100000, commission=0.00015, stake=1, sizer_type="fixed", size_percent=100, tick_type="stock"):
        self.strategy_class = strategy_class
        self.data_feed = data_feed
        self.results = []
        self.logger = setup_logger("grid search optimizer", config_manager.log_level, config_manager.log_to_file)
        
        # 创建BacktestRunner实例
        self.backtest_runner = BacktestRunner(
            cash=cash,
            commission=commission,
            stake=stake,
            sizer_type=sizer_type,
            size_percent=size_percent,
            tick_type=tick_type
        )
    
    def optimize(self, param_grid: Dict[str, List[Any]], metrics=['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'P/L_ratio']) -> pd.DataFrame:
        """
        执行网格搜索优化
        
        Args:
            param_grid: 参数网格，格式如 {'param1': [value1, value2], 'param2': [value3, value4]}
            metrics: 要收集的指标列表
            
        Returns:
            包含所有参数组合和对应指标的DataFrame
        """
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        self.logger.info(f"开始网格搜索，共 {len(param_combinations)} 组参数...")
        
        for i, param_combo in enumerate(param_combinations):
            self.logger.info(f"网格搜索进度: {i+1}/{len(param_combinations)}")
            
            # 构建参数字典
            params = dict(zip(param_names, param_combo))
            
            # 使用BacktestRunner运行单次回测
            result = self.backtest_runner.run(
                strategy_class=self.strategy_class,
                data_feed=self.data_feed,
                params=params
            )

            if result:
                result.update(params)  # 添加参数到结果中
                self.results.append(result)
        
        # 转换为DataFrame并排序
        df_results = pd.DataFrame(self.results)
        if not df_results.empty:
            # 按夏普率降序排列
            if 'sharpe_ratio' in df_results.columns:
                df_results = df_results.sort_values('sharpe_ratio', ascending=False)

        return df_results
    
    def get_best_params(self, metric='sharpe_ratio') -> Dict[str, Any]:
        """获取最佳参数组合"""
        if not self.results:
            return {}
        
        # 直接从results列表中找最佳结果，避免pandas类型转换
        best_result = None
        best_metric_value = float('-inf')
        
        for result in self.results:
            if metric in result and result[metric] > best_metric_value:
                best_metric_value = result[metric]
                best_result = result
        
        if best_result is None:
            return {}

        # 提取参数（排除指标列）
        metric_cols = ['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'P/L_ratio', 'total_trade', 'avg_win', 'avg_loss', 'final_value']
        param_dict = {k: v for k, v in best_result.items() if k not in metric_cols}
        
        return param_dict
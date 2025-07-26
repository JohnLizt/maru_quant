import backtrader as bt
import itertools
import pandas as pd
from typing import Dict, List, Any, Tuple
import warnings

class GridSearchOptimizer:
    def __init__(self, strategy_class, data_feed, cash=100000, commission=0.00015, stake=1, sizer_type="fixed", size_percent=100):
        self.strategy_class = strategy_class
        self.data_feed = data_feed
        self.cash = cash
        self.commission = commission
        self.stake = stake
        self.sizer_type = sizer_type
        self.size_percent = size_percent
        self.results = []
    
    def optimize(self, param_grid: Dict[str, List[Any]], metrics=['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']) -> pd.DataFrame:
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
        
        print(f"开始网格搜索，共 {len(param_combinations)} 组参数...")
        
        for i, param_combo in enumerate(param_combinations):
            print(f"网格搜索进度: {i+1}/{len(param_combinations)}")
            
            # 构建参数字典
            params = dict(zip(param_names, param_combo))
            
            # 运行单次回测
            result = self._run_single_backtest(params)
            if result:
                result.update(params)  # 添加参数到结果中
                self.results.append(result)
        
        # 转换为DataFrame并排序
        df_results = pd.DataFrame(self.results)
        if not df_results.empty:
            # 按利润降序排列
            if 'total_return' in df_results.columns:
                df_results = df_results.sort_values('total_return', ascending=False)

        return df_results
    
    def _run_single_backtest(self, params: Dict[str, Any]) -> Dict[str, float]:
        """运行单次回测"""
        try:
            cerebro = bt.Cerebro()
            
            # 添加数据
            cerebro.adddata(self.data_feed)
            
            # 添加策略和参数
            cerebro.addstrategy(self.strategy_class, **params)
            
            # 设置broker参数
            cerebro.broker.setcash(self.cash)
            cerebro.broker.setcommission(self.commission)
            
            # 根据sizer类型添加相应的sizer
            if self.sizer_type == "fixed":
                cerebro.addsizer(bt.sizers.FixedSize, stake=self.stake)
            elif self.sizer_type == "percents":
                cerebro.addsizer(bt.sizers.PercentSizerInt, percents=self.size_percent)
            
            # 添加分析器
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            
            # 运行回测
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = cerebro.run()
            
            # 提取指标
            strat = result[0]
            final_value = cerebro.broker.getvalue()
            
            return {
                'sharpe_ratio': strat.analyzers.sharpe_ratio.get_analysis().get('sharperatio', 0),
                'total_return': (final_value - self.cash) / self.cash,
                'max_drawdown': strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 0),
                'final_value': final_value
            }
            
        except Exception as e:
            print(f"回测失败，参数: {params}, 错误: {str(e)}")
            return None
    
    def get_best_params(self, metric='total_return') -> Dict[str, Any]:
        """获取最佳参数组合"""
        if not self.results:
            return {}
        
        df_results = pd.DataFrame(self.results)
        if metric not in df_results.columns:
            return {}
        
        # 处理NaN值 - 使用total_return作为备选指标
        if df_results[metric].isna().all():
            print(f"警告: {metric} 全部为NaN，使用 total_return 作为备选指标")
            metric = 'total_return'
            if df_results[metric].isna().all():
                print("错误: 所有指标都为NaN，无法选择最佳参数")
                return {}
        
        # 过滤掉NaN值
        valid_data = df_results.dropna(subset=[metric])
        if valid_data.empty:
            print(f"错误: {metric} 没有有效数据")
            return {}
        
        best_idx = valid_data[metric].idxmax()
        best_result = valid_data.loc[best_idx]
        
        # 提取参数（排除指标列）
        metric_cols = ['sharpe_ratio', 'total_return', 'max_drawdown', 'final_value']
        param_cols = [col for col in df_results.columns if col not in metric_cols]
        
        return {col: best_result[col] for col in param_cols}

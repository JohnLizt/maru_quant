import backtrader as bt
import warnings
from typing import Dict, Any, Optional

from analyzer.sharperatio_30min import SharpeRatio_30min
from analyzer.WinLossRatioAnalyzer import WinLossRatioAnalyzer
from trade.CommissionInfo import comm_ibkr_XAUUSD

def run_backtest_with_params(
    strategy_class,
    data_feed,
    params: Dict[str, Any],
    cash: float = 100000,
    commission: float = 0.00015,
    stake: float = 1,
    sizer_type: str = "fixed",
    size_percent: int = 100,
    tick_type: str = "stock",
) -> Optional[Dict[str, Any]]:
    """
    运行单次回测的通用函数
    
    Args:
        strategy_class: 策略类
        data_feed: 数据源
        params: 策略参数
        cash: 初始资金
        commission: 佣金率
        stake: 固定仓位大小
        sizer_type: 仓位管理类型 ("fixed" 或 "percents")
        size_percent: 百分比仓位大小
        tick_type: 交易品种类型 ("stock" 或其他)
        
    Returns:
        包含回测结果的字典，失败时返回None
    """
    try:
        cerebro = bt.Cerebro()
        
        # 添加数据
        cerebro.adddata(data_feed)
        
        # 添加策略和参数
        cerebro.addstrategy(strategy_class, **params)
        
        # 设置broker参数
        cerebro.broker.setcash(cash)
        
        # 设置佣金
        if tick_type == "CFD":
            cerebro.broker.addcommissioninfo(comm_ibkr_XAUUSD)
        else:
            cerebro.broker.setcommission(commission)
        
        # 设置仓位管理
        if sizer_type == "fixed":
            cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
        elif sizer_type == "percents":
            cerebro.addsizer(bt.sizers.PercentSizerInt, percents=size_percent)
        
        # 添加分析器
        cerebro.addanalyzer(SharpeRatio_30min, _name='sharpe_ratio')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(WinLossRatioAnalyzer, _name='winloss')
        
        # 运行回测
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = cerebro.run()
        
        # 提取结果
        strat = result[0]
        final_value = cerebro.broker.getvalue()
        
        # 构建结果字典
        backtest_result = {
            'sharpe_ratio': strat.analyzers.sharpe_ratio.get_analysis().get('sharperatio', 0),
            'max_drawdown': strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 0),
            'total_return': (final_value - cash) / cash,
            'win_rate': strat.analyzers.winloss.get_analysis().get('win_rate', 0),
            'P/L_ratio': strat.analyzers.winloss.get_analysis().get('P/L_ratio', 0),
        }
        
        return backtest_result
        
    except Exception as e:
        print(f"回测失败，参数: {params}, 错误: {str(e)}")
        return None
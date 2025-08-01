import logging
import backtrader as bt
import warnings
import traceback  # 添加这个导入
from typing import Dict, Any, Optional

from maru_quant.analyzer import SharpeRatio_30min
from maru_quant.analyzer.WinLossRatioAnalyzer import WinLossRatioAnalyzer
from maru_quant.broker.commission_info import comm_ibkr_XAUUSD
from maru_quant.utils.config_manager import config_manager

class BacktestRunner:
    """
    回测运行器类，用于配置和执行回测
    """
    
    def __init__(
        self,
        cash: Optional[float] = None,
        commission: Optional[float] = None,
        stake: Optional[float] = None,
        sizer_type: Optional[str] = None,
        size_percent: Optional[int] = None,
        tick_type: Optional[str] = None,
    ):
        """
        初始化回测运行器
        如果参数为None，则使用配置文件中的默认值
        """
        self.cash = cash or config_manager.cash
        self.commission = commission or config_manager.commission
        self.stake = stake or config_manager.fixed_size_stake
        self.sizer_type = sizer_type or config_manager.sizer_type
        self.size_percent = size_percent or config_manager.size_percent
        self.tick_type = tick_type or config_manager.tick_type

        self.logger = logging.getLogger("main")
    
    @classmethod
    def from_config(cls):
        """从配置文件创建BacktestRunner实例"""
        return cls(**config_manager.get_backtest_params())
    
    def run(
        self,
        strategy_class,
        data_feed,
        params: Dict[str, Any],
        plot = False
    ) -> Optional[Dict[str, Any]]:
        """
        运行单次回测
        
        Args:
            strategy_class: 策略类
            data_feed: 数据源
            params: 策略参数
            
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
            cerebro.broker.setcash(self.cash)
            
            # 设置佣金
            if self.tick_type == "CFD":
                cerebro.broker.addcommissioninfo(comm_ibkr_XAUUSD)
            else:
                cerebro.broker.setcommission(self.commission)
            
            # 设置仓位管理
            if self.sizer_type == "fixed":
                cerebro.addsizer(bt.sizers.FixedSize, stake=self.stake)
            elif self.sizer_type == "percents":
                cerebro.addsizer(bt.sizers.PercentSizerInt, percents=self.size_percent)
            
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
                'total_return': (final_value - self.cash) / self.cash,
                'total_trade': strat.analyzers.winloss.get_analysis().get('total_trades', 0),
                'win_rate': strat.analyzers.winloss.get_analysis().get('win_rate', 0),
                'avg_win': strat.analyzers.winloss.get_analysis().get('avg_win', 0),
                'avg_loss': strat.analyzers.winloss.get_analysis().get('avg_loss', 0),
                'P/L_ratio': strat.analyzers.winloss.get_analysis().get('P/L_ratio', 0),
                'final_value': final_value,
            }
            
            if (plot):
                cerebro.plot(
                    style='candlestick',
                    bgcolor='white',
                    tight_layout=True,
                )
 
            return backtest_result
            
        except Exception as e:
            print(f"回测失败，参数: {params}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("完整调用栈:")
            print(traceback.format_exc())
            
            # 如果有logger，也记录到日志中
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"回测失败，参数: {params}")
                self.logger.error(f"错误: {str(e)}")
                self.logger.error(f"调用栈: {traceback.format_exc()}")
            
            return None
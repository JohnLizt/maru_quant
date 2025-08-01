import time
import backtrader as bt

from maru_quant.live_trading.mt5_gateway import MT5Broker, MT5Data
from maru_quant.strategy.trendtracking.breakout import PivotBreakout
from maru_quant.utils.config_manager import config_manager
mt5_config = config_manager.mt5_config

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    
    # Add MT5 broker
    broker = MT5Broker(
        login=mt5_config.get("account"),
        password=mt5_config.get("password"),
        server=mt5_config.get("server"),
    )
    cerebro.setbroker(broker)
    
    # Add MT5 data
    data = MT5Data(
        symbol=mt5_config.get("symbol"),
        timeframe=bt.TimeFrame.Minutes,
        compression=mt5_config.get("frequency"),
        historical=False
    )
    cerebro.adddata(data)
    
    # Add strategy
    cerebro.addstrategy(PivotBreakout)
    
    # Add sizer
    cerebro.addsizer(bt.sizers.FixedSize, stake=mt5_config.get("fixed_stake"))

    # Run
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

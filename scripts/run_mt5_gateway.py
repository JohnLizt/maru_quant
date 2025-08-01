import time
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from maru_quant.live_trading.mt5_gateway import MT5ConnectionManager, MT5OrderManager
portable = False

if __name__ == "__main__":
    connect_manager = MT5ConnectionManager()
    order_manager = MT5OrderManager("PivotBreakout")
    symbol = "XAUUSDm"

    with connect_manager:
        # 执行交易操作
        order_manager.place_market_order(symbol, 0.01, "SELL")
        time.sleep(2)
        order_manager.close_position(symbol)

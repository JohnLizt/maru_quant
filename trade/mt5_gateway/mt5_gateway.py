import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from trade.mt5_gateway import MT5ConnectionManager, MT5OrderManager
import MetaTrader5 as mt5

current_dir = os.path.dirname(os.path.abspath(__file__))
account_json_path = os.path.join(current_dir, "account.json")
with open(account_json_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

login = config.get("account")
password = config.get("password", "")
server = config.get("server", "")
timeout = config.get("timeout", 10000)
portable = False

if __name__ == "__main__":
    connect_manager = MT5ConnectionManager()
    order_manager = MT5OrderManager("PivotBreakout")
    symbol = "XAUUSDm"

    with connect_manager:
        # 执行交易操作
        order_manager.place_market_order(symbol, 0.01, "BUY")
        order_manager.place_market_order(symbol, 0.01, "SELL")

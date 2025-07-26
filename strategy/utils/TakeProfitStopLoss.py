def takeProfitStopLoss(strategy, take_profit=0.005, stop_loss=0.003):
    current_price = strategy.dataclose[0]
    entry_price = strategy.buyprice
    holding_bars = len(strategy) - strategy.bar_executed
    
    # 计算利润率
    profit_rate = (current_price - entry_price) / entry_price
    
    closed = False
    # 止盈
    if profit_rate >= take_profit:
        strategy.log(f'[止盈]：当前价格 {current_price:.2f}，开仓价格 {entry_price:.2f}，利润率 {profit_rate:.2%}')
        closed = True
    # 止损
    elif profit_rate <= -stop_loss:
        strategy.log(f'[止损]：当前价格 {current_price:.2f}，开仓价格 {entry_price:.2f}，利润率 {profit_rate:.2%}')
        closed = True
    # 超过最大持仓时间
    elif holding_bars >= strategy.params.max_hold_bars:
        strategy.log(f'[到期平仓]：持仓时间 {holding_bars}，利润率 {profit_rate:.2%}')
        closed = True
    
    if closed:
        strategy.order = strategy.close()
    else:
        strategy.log(f'[持仓中]：当前价格 {current_price:.2f}，利润率 {profit_rate:.2%}，持仓时间 {holding_bars}')
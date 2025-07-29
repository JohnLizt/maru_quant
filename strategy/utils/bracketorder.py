import backtrader as bt

def create_bracket_orders(strategy):
    buy_price = strategy.dataclose[0]
    take_profit_price = buy_price + strategy.params.take_profit
    stop_loss_price = buy_price - strategy.params.stop_loss
    strategy.logger.info(f'[多单]：买入价格 {buy_price:.2f}，止盈价格 {take_profit_price:.2f}，止损价格 {stop_loss_price:.2f}')
    return strategy.buy_bracket(exectype=bt.Order.Market, stopprice=stop_loss_price, limitprice=take_profit_price)

def cancel_bracket_orders(strategy):
    """取消所有bracket订单"""
    for order in strategy.bracket_orders[:]:  # 使用切片复制列表避免修改时出错
        if order and order.status in [order.Submitted, order.Accepted, order.Partial]:
            strategy.cancel(order)
    strategy.bracket_orders = []  # 清空列表
from backtrader import OrderBase, Order
import MetaTrader5 as mt5

class MT5Order(OrderBase):
    '''MT5 specific order implementation'''
    
    # Map backtrader order types to MT5 order types
    _MT5OrdTypes = {
        None: mt5.ORDER_TYPE_BUY,  # default
        Order.Market: mt5.ORDER_TYPE_BUY,  # will be adjusted for sell
        Order.Limit: mt5.ORDER_TYPE_BUY_LIMIT,
        Order.Stop: mt5.ORDER_TYPE_BUY_STOP,
        Order.StopLimit: mt5.ORDER_TYPE_BUY_STOP_LIMIT,
    }
    
    def __init__(self, action, **kwargs):
        # 先设置必要的属性，特别是ordtype
        self.action = action  # 'BUY' or 'SELL'
        self.ordtype = self.Buy if action == 'BUY' else self.Sell
        
        # 然后调用父类初始化
        super(MT5Order, self).__init__()
        
        self.mt5_ticket = None  # MT5 order ticket
        self.mt5_request = None  # MT5 order request
        
        # Convert backtrader order type to MT5 order type
        self.mt5_type = self._get_mt5_order_type()
        
    def _get_mt5_order_type(self):
        """Convert backtrader order type to MT5 order type"""
        base_type = self._MT5OrdTypes.get(self.exectype, mt5.ORDER_TYPE_BUY)
        
        # Adjust for SELL orders
        if self.action == 'SELL':
            if base_type == mt5.ORDER_TYPE_BUY:
                return mt5.ORDER_TYPE_SELL
            elif base_type == mt5.ORDER_TYPE_BUY_LIMIT:
                return mt5.ORDER_TYPE_SELL_LIMIT
            elif base_type == mt5.ORDER_TYPE_BUY_STOP:
                return mt5.ORDER_TYPE_SELL_STOP
            elif base_type == mt5.ORDER_TYPE_BUY_STOP_LIMIT:
                return mt5.ORDER_TYPE_SELL_STOP_LIMIT
                
        return base_type
        
    def create_mt5_request(self, symbol):
        """Create MT5 order request"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL if self.exectype == Order.Market else mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": float(abs(self.size)),
            "type": self.mt5_type,
            "deviation": 20,  # Price deviation in points
            "magic": 0,  # EA magic number
            "comment": "backtrader order",
            "type_time": mt5.ORDER_TIME_GTC,  # Good Till Cancelled
            "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
        }
        
        # Set prices based on order type
        if self.exectype == Order.Limit:
            request["price"] = float(self.price)
        elif self.exectype == Order.Stop:
            request["price"] = float(self.price)
        elif self.exectype == Order.StopLimit:
            request["price"] = float(self.price)
            request["stoplimit"] = float(self.pricelimit)
            
        # Set stop loss and take profit if provided
        if hasattr(self, 'stoploss') and self.stoploss:
            request["sl"] = float(self.stoploss)
        if hasattr(self, 'takeprofit') and self.takeprofit:
            request["tp"] = float(self.takeprofit)
            
        self.mt5_request = request
        return request
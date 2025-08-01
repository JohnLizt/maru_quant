import MetaTrader5 as mt5
import threading
import queue
from datetime import datetime, timedelta
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass
from backtrader import TimeFrame, Position
from backtrader.utils import AutoDict

class MetaSingleton(MetaParams):
    '''Metaclass to make a metaclassed class a singleton'''
    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))
        return cls._singleton

class MT5Store(with_metaclass(MetaSingleton, object)):
    '''Store for MetaTrader 5 platform connection'''
    
    BrokerCls = None  # will be set by MetaMT5Broker
    DataCls = None    # will be set by MT5Data
    
    params = (
        ('host', '127.0.0.1'),
        ('port', None),
        ('timeout', 30),
        ('login', None),
        ('password', None),
        ('server', None),
        ('path', None),  # MT5 terminal path
    )
    
    def __init__(self, **kwargs):
        super(MT5Store, self).__init__()
        
        # 正确的方式：逐个设置参数值，而不是使用update()
        for key, value in kwargs.items():
            if hasattr(self.p, key):
                setattr(self.p, key, value)
        
        self._lock = threading.Lock()
        self._orders = {}
        self._positions = {}
        self._account_info = {}
        self._connected = False
        
        # Event queues
        self.orderevents = queue.Queue()
        self.tradeevents = queue.Queue()
        
    def start(self, data=None, broker=None):
        if not self._connected:
            self.connect()
        
        if data is not None:
            self._env = data._env
            
        if broker is not None:
            self.broker = broker
            
    def stop(self):
        if self._connected:
            mt5.shutdown()
            self._connected = False
            
    def connect(self):
        """Connect to MT5 terminal"""
        try:
            if self.p.path:
                if not mt5.initialize(path=self.p.path):
                    print(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize():
                    print(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
                    
            # Login if credentials provided
            if self.p.login and self.p.password and self.p.server:
                if not mt5.login(self.p.login, self.p.password, self.p.server):
                    print(f"MT5 login failed: {mt5.last_error()}")
                    return False
                    
            self._connected = True
            print("MT5 connection established")
            return True
            
        except Exception as e:
            print(f"MT5 connection error: {e}")
            return False
            
    def connected(self):
        return self._connected
        
    def get_account_info(self):
        """Get account information"""
        if not self._connected:
            return None
        return mt5.account_info()
        
    def get_balance(self):
        """Get account balance"""
        account_info = self.get_account_info()
        return account_info.balance if account_info else 0.0
        
    def get_equity(self):
        """Get account equity"""
        account_info = self.get_account_info()
        return account_info.equity if account_info else 0.0
        
    def get_positions(self):
        """Get all open positions"""
        if not self._connected:
            return []
        return mt5.positions_get()
        
    def get_position(self, symbol):
        """Get position for specific symbol"""
        if not self._connected:
            return None
        positions = mt5.positions_get(symbol=symbol)
        return positions[0] if positions else None
        
    def place_order(self, request):
        """Place order through MT5"""
        if not self._connected:
            return None
            
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
        else:
            print(f"Order failed: {result.comment}")
            return None
            
    def cancel_order(self, ticket):
        """Cancel pending order"""
        if not self._connected:
            return False
            
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
        
    def get_rates(self, symbol, timeframe, start_pos=0, count=500):
        """Get historical rates"""
        if not self._connected:
            return None
        return mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        
    def get_symbol_info(self, symbol):
        """Get symbol information"""
        if not self._connected:
            return None
        return mt5.symbol_info(symbol)
import threading
import collections
from datetime import datetime
import MetaTrader5 as mt5

from backtrader import BrokerBase, Order, OrderBase
from backtrader.utils.py3 import with_metaclass, queue
from backtrader.comminfo import CommInfoBase
from backtrader.position import Position
from .mt5store import MT5Store
from .mt5order import MT5Order

class MT5CommInfo(CommInfoBase):
    '''Commission info for MT5'''
    
    def getvaluesize(self, size, price):
        return abs(size) * price
        
    def getoperationcost(self, size, price):
        return abs(size) * price

class MetaMT5Broker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        super(MetaMT5Broker, cls).__init__(name, bases, dct)
        MT5Store.BrokerCls = cls

class MT5Broker(with_metaclass(MetaMT5Broker, BrokerBase)):
    '''MT5 Broker implementation'''
    
    params = ()
    
    def __init__(self, **kwargs):
        super(MT5Broker, self).__init__()
        
        self.mt5 = MT5Store(**kwargs)
        
        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0
        
        self._lock_orders = threading.Lock()
        self.orderbyid = {}  # orders by order id
        self.notifs = queue.Queue()  # order notifications
        self._order_counter = 0
        
    def start(self):
        super(MT5Broker, self).start()
        self.mt5.start(broker=self)
        
        if self.mt5.connected():
            self.startingcash = self.cash = self.mt5.get_balance()
            self.startingvalue = self.value = self.mt5.get_equity()
        else:
            self.startingcash = self.cash = 0.0
            self.startingvalue = self.value = 0.0
            
    def stop(self):
        super(MT5Broker, self).stop()
        self.mt5.stop()
        
    def getcash(self):
        if self.mt5.connected():
            self.cash = self.mt5.get_balance()
        return self.cash
        
    def getvalue(self, datas=None):
        if self.mt5.connected():
            self.value = self.mt5.get_equity()
        return self.value
        
    def getposition(self, data, clone=True):
        """Get position for given data"""
        if not self.mt5.connected():
            return Position()
            
        symbol = data._dataname
        mt5_position = self.mt5.get_position(symbol)
        
        if mt5_position:
            size = mt5_position.volume
            if mt5_position.type == mt5.POSITION_TYPE_SELL:
                size = -size
            price = mt5_position.price_open
            return Position(size=size, price=price)
        else:
            return Position()
            
    def submit(self, order):
        """Submit order to MT5"""
        with self._lock_orders:
            self._order_counter += 1
            order.ref = self._order_counter
            
            symbol = order.data._dataname
            request = order.create_mt5_request(symbol)
            
            result = self.mt5.place_order(request)
            if result:
                order.mt5_ticket = result.order
                order.accept(self)
                self.orderbyid[order.ref] = order
            else:
                order.reject(self)
                
        self.notify(order)
        return order
        
    def cancel(self, order):
        """Cancel order"""
        if hasattr(order, 'mt5_ticket') and order.mt5_ticket:
            success = self.mt5.cancel_order(order.mt5_ticket)
            if success:
                order.cancel()
            else:
                order.reject()
        else:
            order.cancel()
            
        self.notify(order)
        
    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, **kwargs):
        """Create buy order"""
        
        order = MT5Order('BUY', owner=owner, data=data,
                        size=size, price=price, pricelimit=plimit,
                        exectype=exectype, valid=valid, tradeid=tradeid,
                        **kwargs)
        
        order.addcomminfo(self.getcommissioninfo(data))
        return self.submit(order)
        
    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, **kwargs):
        """Create sell order"""
        
        order = MT5Order('SELL', owner=owner, data=data,
                        size=size, price=price, pricelimit=plimit,
                        exectype=exectype, valid=valid, tradeid=tradeid,
                        **kwargs)
        
        order.addcomminfo(self.getcommissioninfo(data))
        return self.submit(order)
        
    def getcommissioninfo(self, data):
        """Get commission info for data"""
        return MT5CommInfo()
        
    def notify(self, order):
        """Notify order status change"""
        self.notifs.put(order.clone())
        
    def get_notification(self):
        """Get next notification"""
        try:
            return self.notifs.get(False)
        except queue.Empty:
            return None
            
    def next(self):
        """Mark notification boundary"""
        self.notifs.put(None)
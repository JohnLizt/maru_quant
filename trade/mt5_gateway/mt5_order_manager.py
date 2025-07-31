import datetime
import os
import MetaTrader5 as mt5
import time
from typing import Optional, Dict, Any
from enum import Enum
from utils.logger import setup_logger

class OrderType(Enum):
    """订单类型枚举"""
    MARKET_BUY = mt5.ORDER_TYPE_BUY
    MARKET_SELL = mt5.ORDER_TYPE_SELL
    LIMIT_BUY = mt5.ORDER_TYPE_BUY_LIMIT
    LIMIT_SELL = mt5.ORDER_TYPE_SELL_LIMIT
    STOP_BUY = mt5.ORDER_TYPE_BUY_STOP
    STOP_SELL = mt5.ORDER_TYPE_SELL_STOP

class TradeAction(Enum):
    """交易动作枚举"""
    DEAL = mt5.TRADE_ACTION_DEAL      # 市价单
    PENDING = mt5.TRADE_ACTION_PENDING # 挂单

class MT5OrderManager:
    def __init__(self, strategy: str):
        self.strategy = strategy
        self.magic_number = 234000 # TODO: get from magic number manager

        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
        filename = f"{log_dir}/mt5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = setup_logger(__name__, level="INFO", log_to_file=True, filename=filename)

    def place_market_order(self, symbol: str, volume: float, 
                          order_type: str, 
                          sl: Optional[float] = None, 
                          tp: Optional[float] = None,
                          deviation: int = 20,
                          comment: str = "Python market order") -> Dict[str, Any]:
        """
        下市价单
        
        Args:
            symbol: 交易品种
            volume: 交易量
            order_type: BUY 或 SELL
            sl: 止损价格
            tp: 止盈价格
            deviation: 允许的价格偏差点数
            comment: 订单备注
        """
        # 检查交易品种
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.logger.error(f"Symbol {symbol} not found")
            return {"success": False, "error": "Symbol not found"}
        
        # 确保品种在市场观察窗口中可见
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                self.logger.error(f"Failed to select symbol {symbol}")
                return {"success": False, "error": "Failed to select symbol"}
        
        # 获取当前价格
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            self.logger.error(f"Failed to get tick data for {symbol}")
            return {"success": False, "error": "No tick data"}
        
        # 根据订单类型设置价格
        if order_type.upper() == "BUY":
            price = tick.ask
            order_type_mt5 = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            order_type_mt5 = mt5.ORDER_TYPE_SELL
        
        # 构建订单请求
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type_mt5,
            "price": price,
            "deviation": deviation,
            "magic": self.magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        # 添加止损止盈
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp
        
        # 发送订单
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Market order failed: {result.retcode}")
            return {
                "success": False, 
                "error": f"Order failed with retcode: {result.retcode}",
                "result": result._asdict()
            }
        
        self.logger.info(f"Market order successful: {order_type} {volume} lots of {symbol} at {price}")
        return {
            "success": True,
            "order_id": result.order,
            "price": result.price,
            "volume": result.volume,
            "result": result._asdict()
        }
    
    def place_limit_order(self, symbol: str, volume: float, 
                         price: float, order_type: str = "BUY_LIMIT",
                         sl: Optional[float] = None, 
                         tp: Optional[float] = None,
                         comment: str = "Python limit order") -> Dict[str, Any]:
        """
        下限价单
        
        Args:
            symbol: 交易品种
            volume: 交易量
            price: 限价
            order_type: BUY_LIMIT 或 SELL_LIMIT
            sl: 止损价格
            tp: 止盈价格
            comment: 订单备注
        """
        # 检查交易品种
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.logger.error(f"Symbol {symbol} not found")
            return {"success": False, "error": "Symbol not found"}
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                self.logger.error(f"Failed to select symbol {symbol}")
                return {"success": False, "error": "Failed to select symbol"}
        
        # 设置订单类型
        if order_type.upper() == "BUY_LIMIT":
            order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
        else:
            order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
        
        # 构建挂单请求
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": order_type_mt5,
            "price": price,
            "magic": self.magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        
        # 添加止损止盈
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp
        
        # 发送订单
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Limit order failed: {result.retcode}")
            return {
                "success": False, 
                "error": f"Order failed with retcode: {result.retcode}",
                "result": result._asdict()
            }
        
        self.logger.info(f"Limit order successful: {order_type} {volume} lots of {symbol} at {price}")
        return {
            "success": True,
            "order_id": result.order,
            "price": price,
            "volume": volume,
            "result": result._asdict()
        }
    
    def close_position(self, symbol: str, position_id: int = None, 
                      volume: float = None) -> Dict[str, Any]:
        """
        平仓
        
        Args:
            symbol: 交易品种
            position_id: 持仓ID（可选）
            volume: 平仓量（可选，不指定则全部平仓）
        """
        # 获取持仓
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            self.logger.warning(f"No positions found for {symbol}")
            return {"success": False, "error": "No positions found"}
        
        # 如果指定了position_id，查找对应持仓
        if position_id:
            position = None
            for pos in positions:
                if pos.ticket == position_id:
                    position = pos
                    break
            if not position:
                self.logger.error(f"Position {position_id} not found")
                return {"success": False, "error": "Position not found"}
        else:
            position = positions[0]  # 使用第一个持仓
        
        # 确定平仓方向和价格
        if position.type == mt5.ORDER_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            close_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        
        # 确定平仓量
        close_volume = volume if volume else position.volume
        
        # 构建平仓请求
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": close_volume,
            "type": close_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": self.magic_number,
            "comment": "Python close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        # 发送平仓请求
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Close position failed: {result.retcode}")
            return {
                "success": False, 
                "error": f"Close failed with retcode: {result.retcode}",
                "result": result._asdict()
            }
        
        self.logger.info(f"Position closed: {close_volume} lots of {symbol}")
        return {
            "success": True,
            "closed_volume": close_volume,
            "result": result._asdict()
        }

# 使用示例
if __name__ == "__main__":
    from mt5_connection_manager import MT5ConnectionManager
    
    with MT5ConnectionManager() as conn:
        order_manager = EnhancedOrderManager()
        
        # 下市价买单
        result = order_manager.place_market_order(
            symbol="XAUUSDm",
            volume=0.01,
            order_type="BUY",
            comment="Test market buy"
        )
        print("Market order result:", result)
        
        # 下限价卖单
        current_price = mt5.symbol_info_tick("XAUUSDm").bid
        limit_result = order_manager.place_limit_order(
            symbol="XAUUSDm",
            volume=0.01,
            price=current_price + 10,  # 高于当前价格10个点
            order_type="SELL_LIMIT",
            comment="Test limit sell"
        )
        print("Limit order result:", limit_result)
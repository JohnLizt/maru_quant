from datetime import datetime
import os
import MetaTrader5 as mt5
from typing import Optional, Dict, Any
from enum import Enum
from maru_quant.utils.logger import setup_logger

class MT5OrderManager:
    """ just sample code """
    def __init__(self, strategy: str):
        self.strategy = strategy
        self.magic_number = 234000 # TODO: get from magic number manager

        self.logger = setup_logger(__name__, level="INFO", log_to_file=True, filename="mt5")

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
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        # 添加止损止盈
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp
        
        # 发送订单
        result = mt5.order_send(request)
        self.logger.info(f"[ORDER SEND]: {order_type} {symbol} {volume} lots at {price} with deviation={deviation} points")
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.print_error(result)
            return {
                "success": False, 
                "error": f"Order failed with retcode: {result.retcode}",
                "result": result._asdict()
            }
        
        self.logger.info(f"[ORDER SUCCESS]: {order_type} {volume} lots of {symbol} at {price}, order_id: {result.order}")
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
        self.logger.info(f"[ORDER SEND]: {order_type} {symbol} {volume} lots at {price}")
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.print_error(result)
            return {
                "success": False, 
                "error": f"Order failed with retcode: {result.retcode}",
                "result": result._asdict()
            }
        
        self.logger.info(f"[ORDER SUCCESS]: {order_type} {volume} lots of {symbol} at {price}, order_id: {result.order}")
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
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # 发送平仓请求
        result = mt5.order_send(request)
        self.logger.info(f"[ORDER SEND]: CLOSE {symbol} {close_volume} lots at {price}")
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.print_error(result)
            return {
                "success": False, 
                "error": f"Close failed with retcode: {result.retcode}",
                "result": result._asdict()
            }
        
        self.logger.info(f"[ORDER SUCCESS]: CLOSE {close_volume} lots of {symbol} at {price}, order_id: {result.order}")
        return {
            "success": True,
            "closed_volume": close_volume,
            "result": result._asdict()
        }

    def print_error(self, result):
        """打印错误信息"""
        self.logger.error(f"[ORDER FAILED]: {result.retcode}")
        result_dict=result._asdict()
        for field in result_dict.keys():
            self.logger.error("   {}={}".format(field,result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field=="request":
                traderequest_dict=result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    self.logger.error("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
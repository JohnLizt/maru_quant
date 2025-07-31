import datetime
import json
import os
import MetaTrader5 as mt5

from utils.logger import setup_logger

class MT5ConnectionManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "config.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.login = self.config.get("account")
        self.password = self.config.get("password", "")
        self.server = self.config.get("server", "")
        self.timeout = self.config.get("timeout", 10000)
        self.portable = False
        self.is_connected = False

        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
        filename = f"{log_dir}/mt5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = setup_logger(__name__, level="INFO", log_to_file=True, filename=filename)
    
    def connect(self) -> bool:
        """建立MT5连接"""
        if self.is_connected:
            return True
            
        try:
            if not mt5.initialize(
                login=self.login, 
                password=self.password, 
                server=self.server, 
                timeout=self.timeout, 
                portable=self.portable
            ):
                self.logger.error(f"MT5 initialize failed, error code: {mt5.last_error()}")
                return False
            
            self.is_connected = True
            self.logger.info("MT5 connection established successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 connection error: {e}")
            return False
    
    def disconnect(self):
        """断开MT5连接"""
        if self.is_connected:
            mt5.shutdown()
            self.is_connected = False
            self.logger.info("MT5 connection closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.connect():
            return self
        else:
            raise ConnectionError("Failed to establish MT5 connection")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
    
    def execute_with_connection(self, func, *args, **kwargs):
        """在连接状态下执行函数"""
        with self:
            return func(*args, **kwargs)
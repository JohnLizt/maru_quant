import json
from typing import Dict, Any

config_path = 'config.json'

class ConfigManager:
    """配置管理器，单例模式管理所有配置"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        # 默认读取项目根目录下的 config.json
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

        # 解析各个配置部分
        self.backtest_config = self._config.get("backtest_config", {})
        self.broker_config = self._config.get("broker_config", {})
        self.logger_config = self._config.get("logger_config", {})
        self.mt5_config = self._config.get("mt5_config", {})
        
        # backtest config
        self.basic_config = self.backtest_config.get("basic", {})
        self.sizer_config = self.backtest_config.get("sizer", {})
        self.optimize_config = self.backtest_config.get("optimize", {})
        self.validation_config = self.backtest_config.get("validation", {})
    
    @property
    def data_file(self) -> str:
        return self.basic_config.get("file")
    
    @property
    def start_date(self) -> str:
        return self.basic_config.get("start_date")
    
    @property
    def end_date(self) -> str:
        return self.basic_config.get("end_date")
    
    @property
    def sizer_type(self) -> str:
        return self.sizer_config.get("sizer", "percents")
    
    @property
    def size_percent(self) -> int:
        return self.sizer_config.get("size_percent", 100)
    
    @property
    def fixed_size_stake(self) -> float:
        return self.sizer_config.get("fixed_size_stake", 1)
    
    @property
    def optimize_mode(self) -> bool:
        return self.optimize_config.get("optimize_mode", False)
    
    @property
    def walk_forward_mode(self) -> bool:
        return self.validation_config.get("walk_forward_mode", False)
    
    @property
    def tick_type(self) -> str:
        return self.broker_config.get("tick_type", "stock")
    
    @property
    def cash(self) -> float:
        return self.broker_config.get("cash", 100000.0)
    
    @property
    def commission(self) -> float:
        return self.broker_config.get("commission", 0.00015)
    
    @property
    def log_level(self) -> str:
        return self.logger_config.get("log_level", "INFO")
    
    @property
    def log_to_file(self) -> bool:
        return self.logger_config.get("log_to_file", True)
    
    def get_backtest_params(self) -> Dict[str, Any]:
        """获取单次回测相关的所有参数"""
        return {
            'cash': self.cash,
            'commission': self.commission,
            'stake': self.fixed_size_stake,
            'sizer_type': self.sizer_type,
            'size_percent': self.size_percent,
            'tick_type': self.tick_type
        }

# 全局配置实例
config_manager = ConfigManager()

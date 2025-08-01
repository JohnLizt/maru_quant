import logging
import os
from datetime import datetime
import backtrader as bt
from maru_quant.utils.config_manager import config_manager

def setup_logger(name: str = "quant", level: str = "INFO", log_to_file: bool = True, filename: str = None):
    """
    设置日志配置
    
    Args:
        name: logger名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
        filename: 自定义日志文件路径和名称，如果为None则使用默认路径
    """
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建file handler
    if log_to_file:
        if filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f"{filename}_{timestamp}.log"
            
            # 确保目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            else:
                raise ValueError("Invalid log file path")
        else:
            # 使用默认路径和时间戳命名
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(project_root, 'log')
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f'log/backtest_{timestamp}.log'
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "quant"):
    """获取已配置的logger"""
    return logging.getLogger(name)

def setup_strategy_logger(strategy, name: str = "strategy", level: str = "INFO"):
    """
    为策略设置专用logger，使用数据时间而不是实际时间
    
    Args:
        strategy: backtrader策略实例，用于获取数据时间
        name: logger名称
        level: 日志级别
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 使用ConfigManager检查是否需要抑制输出
    if config_manager.walk_forward_mode or config_manager.optimize_mode:
        null_handler = logging.NullHandler()
        logger.addHandler(null_handler)
        return logger
    
    # 创建自定义formatter，使用数据时间
    class StrategyFormatter(logging.Formatter):
        def __init__(self, strategy_ref):
            self.strategy_ref = strategy_ref
            super().__init__()
        
        def format(self, record):
            # 获取策略的数据时间
            try:
                data_time = bt.num2date(self.strategy_ref.datas[0].datetime[0])
                record.data_time = data_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                record.data_time = 'N/A'
            
            return f"{record.data_time} - {record.name} - {record.levelname} - {record.getMessage()}"
    
    # 创建console handler，只输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(StrategyFormatter(strategy))
    logger.addHandler(console_handler)
    
    return logger
import logging
import os
from datetime import datetime
import backtrader as bt

def setup_logger(name: str = "quant", level: str = "INFO", log_to_file: bool = True):
    """
    设置日志配置
    
    Args:
        name: logger名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
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
    
    # 创建file handler (如果需要)
    if log_to_file:
        os.makedirs('log', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'log/quant_{timestamp}.log'
        
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
"""
均线策略模块

提供各种均线策略的实现
"""

from .SMA import SMA
from .SMA_V2 import SMA_V2
from .SMA_V3 import SMA_V3

__all__ = ['SMA', 'SMA_V2', 'SMA_V3']
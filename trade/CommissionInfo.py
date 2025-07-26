import backtrader as bt
from utils.config_loader import load_config

def create_commission_info():
    """Factory function to create commission info with config-based parameters"""
    # 从配置文件读取配置
    config = load_config()
    broker_config = config.get('broker_config', {})
    
    # 根据配置设置佣金类型
    if broker_config.get('fixed_commission', True):
        commtype = bt.CommInfoBase.COMM_FIXED
    else:
        commtype = bt.CommInfoBase.COMM_PERC
    
    # 读取杠杆并计算automargin
    leverage = broker_config.get('leverage', 200.0)
    automargin = 1.0 / leverage if leverage > 0 else 0.005
    
    # 动态创建类
    class IBKR_XAUUSD_Commission(bt.CommInfoBase):
        params = (
            ('commtype', commtype),
            ('commission', broker_config.get('commission', 0)),
            ('mult', broker_config.get('multiplier', 100)),  # 黄金期货合约乘数 100盎司
            ('margin', None),  # 使用automargin计算保证金
            ('stocklike', False),  # 期货合约，非股票
            ('automargin', automargin),  # 根据杠杆自动计算
            ('leverage', leverage),
        )
        
        def getoperationcost(self, size, price):
            """重写操作成本计算 - 期货使用保证金而非全额"""
            return abs(size) * self.get_margin(price)
        
        def getvaluesize(self, size, price):
            """重写价值计算 - 期货使用保证金"""
            return abs(size) * self.get_margin(price)
        
        def profitandloss(self, size, price, newprice):
            """重写盈亏计算 - 期货需要乘以合约乘数"""
            return size * (newprice - price) * self.p.mult
    
    return IBKR_XAUUSD_Commission()

# 创建实例
comm_ibkr_XAUUSD = create_commission_info()
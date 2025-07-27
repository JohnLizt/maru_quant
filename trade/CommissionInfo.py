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
    
    # 读取点差
    spread = broker_config.get('spread', 0.16)
    
    # 动态创建类
    class IBKR_XAUUSD_Commission(bt.CommInfoBase):
        params = (
            ('commtype', commtype),
            ('commission', broker_config.get('commission', 0)),
            ('mult', broker_config.get('multiplier', 1)),  # 黄金期货合约乘数 100盎司，这里没用，先不管
            ('margin', None),  # 使用automargin计算保证金
            ('stocklike', True),  # 现货黄金，逻辑类似股票
            ('automargin', automargin),  # 根据杠杆自动计算
            ('spread', spread),  # 添加点差参数
            ('leverage', leverage),  # 添加杠杆参数
        )
        
        def profitandloss(self, size, price, newprice):
            """重写盈亏计算 - 点差"""
            # 基础盈亏计算
            base_pnl = size * (newprice - price)
            
            # 扣除点差成本（每次开仓都要支付点差）
            # 点差成本 = 点差 * size
            spread_cost = abs(size) * self.p.spread

            return base_pnl - spread_cost
    
    return IBKR_XAUUSD_Commission()

# 创建实例
comm_ibkr_XAUUSD = create_commission_info()
import backtrader as bt

class PivotHigh(bt.Indicator):
    '''
    检测局部极大值(Pivot High), 延迟N bar输出。
    维护最近的pivot high队列
    '''
    # 固定创建最大可能的lines数量
    lines = ('resist0', 'resist1', 'resist2', 'resist3', 'resist4', 'resist5', 'resist6', 'resist7', 'resist8', 'resist9')
    params = (('window', 16), ('max_resists', 5))

    plotlines = dict(
        resist0=dict(_plotskip=False, color='red', linestyle='-', linewidth=2),
        resist1=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist2=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist3=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist4=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist5=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist6=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist7=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist8=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist9=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
    )

    def __init__(self):
        self.addminperiod(self.p.window * 2 + 1)
        self.plotinfo.plot = True
        self.plotinfo.subplot = False
        self.pivot_queue = []  # 简单队列，存储(价格, bar_index)

    def next(self):
        n = self.p.window
        center_idx = -n
        center_close = self.data.close[center_idx]
        is_pivot = True
        
        # 检查左侧N根
        for i in range(1, n+1):
            if center_close <= self.data.close[center_idx - i]:
                is_pivot = False
                break
        # 检查右侧N根
        if is_pivot:
            for i in range(1, n+1):
                if center_close <= self.data.close[center_idx + i]:
                    is_pivot = False
                    break
        
        # 如果是新的pivot high，更新队列
        if is_pivot:
            current_bar = len(self)
            # 将新pivot添加到队列末尾
            self.pivot_queue.append((center_close, current_bar))
            # 限制队列大小
            if len(self.pivot_queue) > self.p.max_resists:
                self.pivot_queue.pop(0)  # 移除最旧的pivot
        
        # 输出当前队列中的pivot高点，只使用max_resists数量的lines
        for i in range(min(self.p.max_resists, 10)):  # 限制在最大10个
            if i < len(self.pivot_queue):
                getattr(self.lines, f'resist{i}')[0] = self.pivot_queue[-(i+1)][0]  # 倒序输出，最新的在resist0
            else:
                getattr(self.lines, f'resist{i}')[0] = float('nan')
        
        # 将未使用的lines设为NaN
        for i in range(self.p.max_resists, 10):
            getattr(self.lines, f'resist{i}')[0] = float('nan')
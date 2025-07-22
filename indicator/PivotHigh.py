import backtrader as bt

class PivotHigh(bt.Indicator):
    '''
    检测局部极大值(Pivot High), 延迟N bar输出。
    使用单调递减栈维护多个pivot high
    lines:
        resist0: 最近的pivot high
        resist1: 第二近的pivot high
        resist2: 第三近的pivot high
        resist3: 第四近的pivot high
        resist4: 第五近的pivot high
    '''
    lines = ('resist0', 'resist1', 'resist2', 'resist3', 'resist4')
    params = (('window', 2), ('threshold', 0.1))  # 增加区间阈值参数，默认10%

    plotlines = dict(
        resist0=dict(_plotskip=False, color='red', linestyle='-', linewidth=2),
        resist1=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist2=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist3=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
        resist4=dict(_plotskip=False, color='red', linestyle='-', linewidth=1),
    )

    def __init__(self):
        self.addminperiod(self.p.window * 2 + 1)
        self.plotinfo.plot = True
        self.plotinfo.subplot = False
        self.pivot_stack = []  # 单调递减栈，存储(价格, bar_index)

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
        
        # 如果是新的pivot high，更新栈
        if is_pivot:
            current_bar = len(self)
            # 维护单调递减栈：只有新pivot高于栈顶且超过阈值时，才出栈
            while self.pivot_stack and center_close > self.pivot_stack[-1][0] * (1 + self.p.threshold):
                self.pivot_stack.pop()
            # 将新pivot入栈
            self.pivot_stack.append((center_close, current_bar))
            # 限制栈大小为5
            if len(self.pivot_stack) > 5:
                self.pivot_stack = self.pivot_stack[-5:]
        
        # 输出当前栈中的pivot高点
        for i in range(5):
            line_name = f'resist{i}'
            if len(self.pivot_stack) > i:
                getattr(self.lines, line_name)[0] = self.pivot_stack[-(i+1)][0]
            else:
                getattr(self.lines, line_name)[0] = float('nan')

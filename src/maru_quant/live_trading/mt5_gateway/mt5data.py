from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import queue

from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, num2date
from .mt5store import MT5Store

class MT5Data(DataBase):
    '''MT5 data feed'''
    
    params = (
        ('symbol', ''),
        ('timeframe', mt5.TIMEFRAME_M1),
        ('compression', 1),
        ('historical', False),
        ('backfill_start', True),
        ('backfill', True),
        ('latethrough', False),   # 是否允许迟到的数据通过
        ('qcheck', 0.5),         # 检查队列的超时时间
    )
    
    # 状态机状态定义 - 去掉 _ST_FROM
    _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(4)
    
    def __init__(self, **kwargs):
        super(MT5Data, self).__init__()
        
        self.mt5 = MT5Store(**kwargs)
        self._dataname = self.p.symbol
        self.symbol = self.p.symbol
        
        # Map backtrader timeframes to MT5 timeframes
        self._timeframe_map = {
            (TimeFrame.Minutes, 1): mt5.TIMEFRAME_M1,
            (TimeFrame.Minutes, 5): mt5.TIMEFRAME_M5,
            (TimeFrame.Minutes, 15): mt5.TIMEFRAME_M15,
            (TimeFrame.Minutes, 30): mt5.TIMEFRAME_M30,
            (TimeFrame.Minutes, 60): mt5.TIMEFRAME_H1,    # 1小时 = 60分钟
            (TimeFrame.Minutes, 240): mt5.TIMEFRAME_H4,   # 4小时 = 240分钟
            (TimeFrame.Days, 1): mt5.TIMEFRAME_D1,
            (TimeFrame.Days, 7): mt5.TIMEFRAME_W1,        # 1周 = 7天
            (TimeFrame.Days, 30): mt5.TIMEFRAME_MN1,      # 1月 ≈ 30天
        }
        
        # Get MT5 timeframe
        tf_key = (self.p.timeframe, self.p.compression)
        self.mt5_timeframe = self._timeframe_map.get(tf_key, mt5.TIMEFRAME_M1)
        
        # 初始化状态和数据结构
        self._data = []
        self._idx = 0
        self._state = None
        self._statelivereconn = False
        self._subcription_valid = False
        self._storedmsg = dict()
        self.qlive = None
        self.qhist = None
        
    def start(self):
        super(MT5Data, self).start()
        
        # 初始化队列和状态
        self.qlive = queue.Queue()
        self.qhist = None
        
        # 设置初始状态
        self._state = self._ST_START
        self._statelivereconn = False
        self._subcription_valid = False
        self._storedmsg = dict()
        
        # 启动 MT5Store
        self.mt5.start(data=self)
        
        if not self.mt5.connected():
            self.put_notification(self.DISCONNECTED)
            return
            
        self.put_notification(self.CONNECTED)
        
        if self._state == self._ST_START:
            self._st_start()
            
    def stop(self):
        super(MT5Data, self).stop()
        self.mt5.stop()
        
    def _st_start(self):
        """处理开始状态"""
        if self.p.historical:
            # 纯历史数据模式
            self.put_notification(self.DELAYED)
            self._load_historical_data()
            self._state = self._ST_HISTORBACK
            return True
            
        # 实时数据模式
        if not self.mt5.connected():
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_OVER
            return False
            
        self._statelivereconn = self.p.backfill_start
        if self.p.backfill_start:
            self.put_notification(self.DELAYED)
            # 先加载历史数据进行回填
            self._load_historical_data()
            
        self._state = self._ST_LIVE
        return True
        
    def _load_historical_data(self):
        """Load historical data from MT5"""
        if not self.mt5.connected():
            return False
            
        # 计算需要回填的数据量
        count = 1000  # 默认获取1000条数据 TODO: check
        if self.p.backfill_start and not self.p.historical:
            # 实时模式下的初始回填，可以根据需要调整数量
            count = 500
            
        # Get historical rates
        rates = self.mt5.get_rates(self.symbol, self.mt5_timeframe, 0, count)
        
        if rates is not None and len(rates) > 0:
            # Convert to pandas DataFrame for easier handling
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Convert to backtrader format and store
            historical_data = []
            for _, row in df.iterrows():
                historical_data.append([
                    date2num(row['time']),  # datetime
                    row['open'],            # open
                    row['high'],            # high  
                    row['low'],             # low
                    row['close'],           # close
                    row['tick_volume'],     # volume
                    0,                      # openinterest
                ])
            
            # 如果是历史模式，直接设置数据
            if self.p.historical:
                self._data = historical_data
                self._idx = 0
            else:
                # 实时模式下，将历史数据加入队列
                self.qhist = queue.Queue()
                for bar_data in historical_data:
                    self.qhist.put(bar_data)
                    
            return True
            
        return False
        
    def _load(self):
        """主要的数据加载方法 - 状态机"""
        if self._state == self._ST_OVER:
            return False
            
        while True:
            if self._state == self._ST_LIVE:
                return self._load_live()
                
            elif self._state == self._ST_HISTORBACK:
                return self._load_historical()
                
            elif self._state == self._ST_START:
                if not self._st_start():
                    return False
                continue  # 继续处理新状态
                
            else:
                return False
                
    def _load_live(self):
        """处理实时数据状态"""
        try:
            # 首先检查是否有历史回填数据
            if self.qhist is not None:
                try:
                    bar_data = self.qhist.get_nowait()
                    return self._load_bar_data(bar_data)
                except queue.Empty:
                    # 历史回填完成
                    self.qhist = None
                    if self._statelivereconn:
                        self._statelivereconn = False
                        self.put_notification(self.LIVE)
            
            # 处理实时数据
            try:
                msg = self.qlive.get(timeout=self.p.qcheck)
            except queue.Empty:
                return None  # 没有数据，继续等待
                
            if msg is None:
                # 连接断开信号
                self.put_notification(self.DISCONNECTED)
                if self.p.backfill:
                    # 尝试重连和回填
                    if self.mt5.connected():
                        self._load_historical_data()  # 回填断开期间的数据
                return None
                
            # 处理实时数据消息
            return self._process_live_message(msg)
            
        except Exception as e:
            self.put_notification(self.DISCONNECTED)
            return False
            
    def _load_historical(self):
        """处理历史数据回填状态"""
        if self._idx >= len(self._data):
            self._state = self._ST_OVER
            return False
            
        data_point = self._data[self._idx]
        self._idx += 1
        
        return self._load_bar_data(data_point)
        
    def _load_bar_data(self, bar_data):
        """加载K线数据到lines"""
        dt = bar_data[0]  # datetime
        
        # 检查时间顺序
        if (len(self.lines.datetime) > 0 and 
            dt <= self.lines.datetime[-1] and 
            not self.p.latethrough):
            return False  # 时间倒序，跳过
            
        # 设置数据到lines
        self.lines.datetime[0] = dt
        self.lines.open[0] = bar_data[1]
        self.lines.high[0] = bar_data[2]
        self.lines.low[0] = bar_data[3]
        self.lines.close[0] = bar_data[4]
        self.lines.volume[0] = bar_data[5]
        self.lines.openinterest[0] = bar_data[6]
        
        return True
        
    def _process_live_message(self, msg):
        """处理实时消息"""
        # 这里需要根据MT5的实时数据格式来实现
        # 暂时返回None，需要MT5Store提供实时数据接口
        return None
        
    def haslivedata(self):
        """检查是否有实时数据可用"""
        return bool(self._storedmsg or (self.qlive and not self.qlive.empty()))
        
    def islive(self):
        """Check if data feed is live"""
        return not self.p.historical
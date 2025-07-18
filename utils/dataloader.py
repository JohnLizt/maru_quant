import os
import backtrader as bt
import pandas as pd

def load_data(dataFile, start_date=None, end_date=None):
    # 自动从文件名提取 interval
    # 文件名格式: data/OANDA_XAUUSD, 60_76817.csv
    base = os.path.basename(dataFile)
    parts = base.split('_')
    if len(parts) > 1:
        # 取最后一个下划线前的部分，再取逗号后第一个字段
        left = parts[-2]
        if ',' in left:
            interval_str = left.split(',')[-1].strip()
        else:
            interval_str = left.strip()
    else:
        interval_str = "1D"

    # 判断时间周期
    if interval_str.upper().endswith('D'):
        tf = bt.TimeFrame.Days
        comp = 1
    else:
        try:
            comp = int(interval_str)
            tf = bt.TimeFrame.Minutes
        except Exception:
            tf = bt.TimeFrame.Days
            comp = 1

    time_col = "time"  # 你的数据首列为'time'

    # Load data
    dataframe = pd.read_csv(dataFile, parse_dates=[time_col], index_col=time_col)
    dataframe.sort_index(inplace=True)

    # 修正Volume的NaN问题，如果没有Volume列则补充
    if 'Volume' not in dataframe.columns:
        dataframe['Volume'] = 0

    # Filter by start_date and end_date if provided
    df = dataframe
    if start_date:
        df = df[df.index >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df.index <= pd.to_datetime(end_date)]

    # 自动适配时间周期
    data_feed = bt.feeds.PandasData(
        dataname=df,
        timeframe=tf,
        compression=comp,
        datetime=None  # 首列为索引，自动识别
    )
    return data_feed
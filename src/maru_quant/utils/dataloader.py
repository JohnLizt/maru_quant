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

    # Load data - 自动使用第一列作为时间列
    dataframe = pd.read_csv(dataFile, parse_dates=[0], index_col=0)
    dataframe.sort_index(inplace=True)

    # 修正Volume的NaN问题，如果没有Volume列则补充
    if 'Volume' not in dataframe.columns:
        dataframe['Volume'] = 0

    # 统一索引为UTC时区
    if dataframe.index.tz is None:
        dataframe.index = dataframe.index.tz_localize('UTC')
    else:
        dataframe.index = dataframe.index.tz_convert('UTC')

    # Filter by start_date and end_date if provided
    df = dataframe
    if start_date:
        # 保证start_date带有UTC时区
        start_dt = pd.to_datetime(start_date).tz_localize('UTC')
        df = df[df.index >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date).tz_localize('UTC')
        df = df[df.index <= end_dt]

    # 自动适配时间周期
    data_feed = bt.feeds.PandasData(
        dataname=df,
        timeframe=tf,
        compression=comp,
        datetime=None  # 首列为索引，自动识别
    )
    return data_feed
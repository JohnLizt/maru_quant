import os
import backtrader as bt
import pandas as pd

def load_data(dataFile, start_date=None, end_date=None):
    # 自动从文件名提取 interval
    # 文件名格式: data/SYMBOL_INTERVAL_DATE.csv
    base = os.path.basename(dataFile)
    parts = base.split('_')
    interval = parts[1] if len(parts) > 2 else "1d"

    # 判断首列和时间周期
    if interval.endswith("min"):
        time_col = "datetime"
        tf = bt.TimeFrame.Minutes
        comp = int(interval.replace("min", ""))
    elif interval.endswith("h"):
        time_col = "datetime"
        tf = bt.TimeFrame.Minutes
        comp = int(interval.replace("h", "")) * 60
    elif interval.endswith("d"):
        time_col = "date"
        tf = bt.TimeFrame.Days
        comp = 1
    else:
        # 默认日线
        time_col = "date"
        tf = bt.TimeFrame.Days
        comp = 1

    # Load data
    dataframe = pd.read_csv(dataFile, parse_dates=[time_col], index_col=time_col)
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
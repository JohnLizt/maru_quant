import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import json

from downloader.config_loader import load_config

# 1. 设置时间范围：根据配置的下载方式决定
start_date = None
end_date = None
download_mode = "default"

config = load_config().get("download_config", {}).get("yf_config", {})
download_mode = config.get("download_mode", "default")
ticker = config.get("ticker")
if download_mode == "manual":
    start_date = config.get("download_start_date")
    end_date = config.get("download_end_date")

if download_mode == "manual" and start_date is not None and end_date is not None:
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
else:
    today = datetime.today()
    end_date = today.replace(day=1)  # 本月第一天
    start_date = end_date.replace(year=end_date.year - 1)

# 2. 下载股票数据（例如：AAPL），会屏蔽中国IP，建议使用美国节点，开启proxy
df = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

# 3. 打印预览
print(df.head())

# 4. 保存为 CSV 文件，格式适配 Backtrader
if download_mode == "manual" and start_date is not None and end_date is not None:
    csv_filename = f"data/{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
else:
    csv_filename = f"data/{ticker}_last_year.csv"
    
# 重新排列并重命名列
df_bt = df.rename(columns={
    'Open': 'Open',
    'High': 'High',
    'Low': 'Low',
    'Close': 'Close',
    'Volume': 'Volume'
})
df_bt = df_bt[['Open', 'High', 'Low', 'Close', 'Volume']]
df_bt.index.name = 'Date'
df_bt.reset_index(inplace=True)
df_bt.to_csv(csv_filename, index=False)

# 删除第二行（ticker名），只保留标准头和数据
with open(csv_filename, 'r') as f:
    lines = f.readlines()
with open(csv_filename, 'w') as f:
    f.write(lines[0])  # header
    f.writelines(lines[2:])  # skip line 2, write data

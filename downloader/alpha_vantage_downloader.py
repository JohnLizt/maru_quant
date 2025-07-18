import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import pandas as pd
from datetime import datetime
import json

from utils.config_loader import load_config

config = load_config().get("download_config", {}).get("alpha_config", {})
api_key = config.get("api_key")  # 在这里填入你从 Alpha Vantage 获得的 API 密钥
symbol = config.get("symbol") # 标的
all_history = config.get("all_history", False)  # 是否下载全部历史数据
time_series = config.get("time_series", "TIME_SERIES_DAILY")  # 默认使用日线数据
interval = "1d" # 默认时间间隔为 1 天

# Alpha Vantage API 地址
url = f"https://www.alphavantage.co/query?function={time_series}&symbol={symbol}"
if time_series == "TIME_SERIES_INTRADAY":
    interval = config.get("interval", "30min")  # 默认使用 30 分钟数据
    url += f"&interval={interval}"
if all_history:
    url += "&outputsize=full"  # 获取全部历史数据
url += f"&apikey={api_key}"
print(f"请求 URL: {url}")

# 发起请求
response = requests.get(url)
data = response.json()
print("API Response Status Code:", response.status_code)

# 错误信息处理
if "Error Message" in data:
    print("API Error:", data["Error Message"])
elif 'Time Series (Daily)' in data:
    # 获取数据并转换为 DataFrame
    df = pd.DataFrame(data['Time Series (Daily)']).T  # 转置数据
    # 重命名列
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    })
    # 转换为数值类型
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # 转换日期格式
    df.index = pd.to_datetime(df.index)

    # 显示数据
    print(df.head())

    # 添加 Date 字段
    df = df.reset_index().rename(columns={'index': 'Date'})

    # 倒序排列
    df = df.sort_index(ascending=False)

    # 保存为 CSV 文件
    timezone = "all_history" if all_history else "latest"
    df.to_csv(f"data/{symbol}_{interval}_{timezone}.csv", index=False)
else:
    print("无法获取数据，检查 API 请求是否正确。")

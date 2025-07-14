import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from twelvedata import TDClient
import pandas as pd

from downloader.config_loader import load_config
from datetime import datetime

# 读取配置
config = load_config().get("download_config", {}).get("twelvedata_config", {})
symbol = config.get("symbol", "XAU/USD")  # 默认标的
interval = config.get("interval", "1h")  # 默认时间间隔为 1h
start_datetime = config.get("start_datetime")  # 默认开始日期为 UTC 当前时间前一个月
if not start_datetime:
    start_datetime = (datetime.utcnow() - pd.DateOffset(months=1)).strftime('%Y-%m-%d %H:%M:%S')
end_datetime = config.get("end_datetime")  # 默认结束日期为 UTC 当前时间
output_size = config.get("output_size", 5000)  # 最大5000条，如果数据量大可分段请求
API_KEY = config.get("api_key")  # 在这里填入你从 Twelve Data 获得的 API 密钥

# 创建客户端对象
td = TDClient(apikey=API_KEY)

# 请求OHLCV 数据
ts = td.time_series(
    symbol=symbol,
    interval=interval,
    start_date=start_datetime,
    end_date=end_datetime,
    outputsize=output_size,  # 最大5000条，如果数据量大可分段请求
    timezone="UTC"
)

# 以 pandas DataFrame 格式获取
df = ts.as_pandas()
# 按时间排序
df.sort_index(inplace=True)

# 删除所有日内时间为 21:00:00 的数据
df = df[df.index.time != pd.to_datetime("21:00:00").time()]

# 保存为 CSV 文件
safe_symbol = symbol.replace("/", "").replace("_", "")
start_str = pd.to_datetime(start_datetime).date().isoformat() if start_datetime else "last_year"
end_str = pd.to_datetime(end_datetime).date().isoformat() if end_datetime else "now"
df.to_csv(f"data/{safe_symbol}_{interval}_{start_str}-{end_str}.csv", index=True)

print("✅ 已保存:", df.head())

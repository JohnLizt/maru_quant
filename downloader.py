import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 1. 设置时间范围：最近3个月（不包括本月）
today = datetime.today()
end_date = today.replace(day=1)  # 本月第一天
# 上上上个月第一天
start_month = (end_date.month - 3 - 1) % 12 + 1
start_year = end_date.year if end_date.month > 3 else end_date.year - 1
start_date = end_date.replace(year=start_year, month=start_month, day=1)

# 2. 下载股票数据（例如：AAPL），会屏蔽中国IP
ticker = "AAPL"
df = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

# 3. 打印预览
print(df.head())

# 4. 保存为 CSV 文件，格式适配 Backtrader
csv_filename = f"data/{ticker}_last_season.csv"
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

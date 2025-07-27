import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from twelvedata import TDClient
import pandas as pd
from datetime import datetime, timedelta

from utils.config_loader import load_config

# 读取配置
config = load_config().get("download_config", {}).get("twelvedata_config", {})
symbol = config.get("symbol", "XAU/USD")  # 默认标的
interval = config.get("interval", "30min")  # 默认时间间隔为 1h
start_datetime = config.get("start_datetime")  # 默认开始日期为 UTC 当前时间前一个月
if not start_datetime:
    start_datetime = (datetime.utcnow() - pd.DateOffset(months=1)).strftime('%Y-%m-%d %H:%M:%S')
end_datetime = config.get("end_datetime")  # 默认结束日期为 UTC 当前时间
output_size = config.get("output_size", 5000)  # 最大5000条，如果数据量大可分段请求
API_KEY = config.get("api_key")  # 在这里填入你从 Twelve Data 获得的 API 密钥
MAX_RETRIES = config.get("max_retries", 3)  # 最大重试次数
BASE_DELAY = config.get("base_delay", 8)  # 基础延迟时间

def calculate_segments(start_datetime, end_datetime, interval):
    """计算需要分段下载的时间段"""
    start = pd.to_datetime(start_datetime)
    end = pd.to_datetime(end_datetime)
    
    # 根据不同间隔估算每段的时间长度（保守估计，确保不超过5000条）
    interval_minutes = {
        '1min': 1, '5min': 5, '15min': 15, '30min': 30, '45min': 45,
        '1h': 60, '2h': 120, '4h': 240, '1day': 1440, '1week': 10080, '1month': 43200
    }
    
    minutes_per_record = interval_minutes.get(interval, 60)  # 默认1小时
    max_records_per_segment = 4000  # 保守设置为4000，留出缓冲
    
    # 计算每段的时间长度
    segment_duration = timedelta(minutes=minutes_per_record * max_records_per_segment)
    
    segments = []
    current_start = start
    
    while current_start < end:
        current_end = min(current_start + segment_duration, end)
        segments.append((current_start, current_end))
        current_start = current_end
    
    return segments

def downloadonce():
    # 创建客户端对象
    td = TDClient(apikey=API_KEY)
    
    # 计算是否需要分段下载
    segments = calculate_segments(start_datetime, end_datetime, interval)
    
    if len(segments) == 1:
        print(f"📥 单次下载: {start_datetime} 到 {end_datetime}")
        df = download_segment_with_retry(td, start_datetime, end_datetime)
        if df is None:
            print("❌ 下载失败")
            return
    else:
        print(f"📥 分段下载: 共 {len(segments)} 段")
        all_dataframes = []
        
        for i, (seg_start, seg_end) in enumerate(segments, 1):
            print(f"  下载第 {i}/{len(segments)} 段: {seg_start} 到 {seg_end}")
            
            df_segment = download_segment_with_retry(
                td, 
                seg_start.strftime('%Y-%m-%d %H:%M:%S'),
                seg_end.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            if df_segment is not None and not df_segment.empty:
                all_dataframes.append(df_segment)
                print(f"    ✅ 第 {i} 段下载成功，获得 {len(df_segment)} 条记录")
            else:
                print(f"    ❌ 第 {i} 段下载失败，跳过")
            
            # 段间延迟
            if i < len(segments):
                time.sleep(BASE_DELAY)
        
        if all_dataframes:
            # 合并所有数据
            df = pd.concat(all_dataframes)
            # 去重并排序
            df = df[~df.index.duplicated(keep='first')]
            df.sort_index(inplace=True)
            print(f"✅ 合并完成，共 {len(df)} 条记录")
        else:
            print("❌ 所有分段下载失败")
            return

    # 保存为 CSV 文件
    save_dataframe(df, start_datetime, end_datetime)

def download_segment(td_client, start_datetime, end_datetime):
    """下载单个时间段的数据"""
    ts = td_client.time_series(
        symbol=symbol,
        interval=interval,
        start_date=start_datetime,
        end_date=end_datetime,
        outputsize=output_size,
        timezone="UTC"
    )
    
    df = ts.as_pandas()
    return df

def download_segment_with_retry(td_client, start_datetime, end_datetime):
    """带重试机制的分段下载"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            df = download_segment(td_client, start_datetime, end_datetime)
            return df
        except Exception as e:
            print(f"    ⚠️ 第 {attempt} 次尝试失败: {e}")
            if attempt < MAX_RETRIES:
                # 指数退避延迟
                delay = BASE_DELAY * (2 ** (attempt - 1))
                print(f"    🔄 等待 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                print(f"    ❌ 达到最大重试次数 {MAX_RETRIES}，放弃下载")
                return None
    
    return None

def save_dataframe(df, start_datetime, end_datetime):
    """保存DataFrame到CSV文件"""
    safe_symbol = symbol.replace("/", "").replace("_", "")
    start_str = pd.to_datetime(start_datetime).date().isoformat() if start_datetime else "last_year"
    end_str = pd.to_datetime(end_datetime).date().isoformat() if end_datetime else "now"
    
    filename = f"data/{safe_symbol}_{interval}_{start_str}-{end_str}.csv"
    df.to_csv(filename, index=True)
    
    print(f"✅ 已保存到 {filename}")
    print(f"📊 数据概览:")
    print(f"  记录数: {len(df)}")
    print(f"  时间范围: {df.index.min()} 到 {df.index.max()}")
    print(f"  前5行:\n{df.head()}")

if __name__ == "__main__":
    downloadonce()
    print("下载完成！")
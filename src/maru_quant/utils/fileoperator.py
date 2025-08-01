import re

def extract_dates_from_filename(filename):
    """从文件名中提取起止时间"""
    if not filename:
        return None, None
    
    # 匹配日期格式：YYYY-MM-DD-YYYY-MM-DD
    pattern = r'(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, filename)
    
    if match:
        start_date = match.group(1)
        end_date = match.group(2)
        return start_date, end_date
    else:
        return None, None
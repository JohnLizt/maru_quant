import json
import os

def load_config(config_path=None):
    # 默认读取项目根目录下的 config.json
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

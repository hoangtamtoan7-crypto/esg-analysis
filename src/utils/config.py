"""全局配置"""
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
EXTRACTED_DIR = DATA_DIR / "extracted"
OUTPUT_DIR = DATA_DIR / "output"

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 预算控制 (元)
MAX_API_COST = 80  # 留20元buffer

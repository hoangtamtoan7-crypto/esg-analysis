"""Streamlit Cloud 入口 — ESG数据智能提取与分析系统"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 以主模块身份执行 src/app/main.py
# exec方式确保Streamlit正确识别所有st.xxx()调用
app_path = BASE_DIR / "src" / "app" / "main.py"
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 必须传入 __file__ 因为 main.py 内部用 Path(__file__).parent.parent.parent 定位项目根目录
exec(compile(code, str(app_path), "exec"), {
    "__name__": "__main__",
    "__file__": str(app_path),
})

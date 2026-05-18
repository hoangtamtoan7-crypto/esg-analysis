"""Streamlit Cloud 入口"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 导入主应用模块 — Streamlit会自动执行模块级别的 st.xxx() 调用
import src.app.main  # noqa: F401

"""ESG智能分析系统入口"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(Path(__file__).parent / "src" / "app" / "main.py"))

"""ESG报告智能提取与分析系统 - 一键运行入口

使用方法:
    python run.py download     # 步骤1: 下载ESG报告
    python run.py preprocess   # 步骤2: 预处理PDF
    python run.py extract      # 步骤3: 大模型提取指标
    python run.py validate     # 步骤4: 校验提取结果
    python run.py db-import    # 步骤5: 导入数据库
    python run.py analyze      # 步骤6: ESG数据分析
    python run.py app          # 步骤7: 启动可视化应用
    python run.py all          # 一键运行全流程
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent


def check_api_key():
    """检查DeepSeek API Key是否设置"""
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        print("=" * 60)
        print("⚠ 未设置DEEPSEEK_API_KEY环境变量")
        print("=" * 60)
        print("\n请设置您的DeepSeek API Key：")
        print('  PowerShell: $env:DEEPSEEK_API_KEY="sk-xxx"')
        print('  CMD: set DEEPSEEK_API_KEY=sk-xxx')
        print("\n获取API Key: https://platform.deepseek.com/")
        print("=" * 60)
        return False
    return True


def cmd_download():
    """下载ESG报告"""
    from src.collector.downloader import ESGReportDownloader
    downloader = ESGReportDownloader()
    downloader.run(limit=None, delay=2.0)


def cmd_preprocess():
    """预处理PDF"""
    from src.preprocessor.pdf_parser import PDFParser
    parser = PDFParser()
    results = parser.batch_parse()
    print(f"\n预处理完成: {len(results)}个PDF已处理")


def cmd_extract():
    """大模型提取"""
    if not check_api_key():
        return
    from src.extractor.extractor import ESGExtractor
    extractor = ESGExtractor()
    results = extractor.batch_extract()
    print(f"\n提取完成: {len(results)}个报告")
    print(extractor.get_cost_summary())


def cmd_validate():
    """校验提取结果"""
    from src.extractor.extractor import validate_existing
    validate_existing()


def cmd_db_import():
    """导入数据到数据库"""
    from src.utils.db import Database, import_results_from_json
    db = Database()
    stats = import_results_from_json(db)
    print(f"\n数据库导入统计:")
    print(f"  公司: {stats['companies']}")
    print(f"  报告: {stats['reports']}")
    print(f"  定量值: {stats['values']}")
    print(f"  定性值: {stats['texts']}")
    if stats["errors"]:
        print(f"  错误: {len(stats['errors'])}")
        for err in stats["errors"][:5]:
            print(f"    - {err}")

    # 显示数据库统计
    s = db.get_statistics()
    print(f"\n数据库整体统计: {s}")


def cmd_analyze():
    """ESG数据分析"""
    from src.analyzer import run_full_analysis
    result = run_full_analysis()
    print(f"\n分析完成！")
    print(f"  ESG评分TOP5:")
    for _, row in result['scores'].head(5).iterrows():
        print(f"    {int(row['排名'])}. {row['公司']} ({row['行业']}) — ESG综合: {row['ESG综合']:.3f}")
    print(f"  报告: {result['report_path']}")


def cmd_app():
    """启动可视化应用"""
    import subprocess
    app_path = BASE_DIR / "src" / "app" / "main.py"
    subprocess.run(["streamlit", "run", str(app_path)])


def cmd_all():
    """一键全流程"""
    print("=" * 60)
    print("ESG报告数据智能提取与分析系统")
    print("=" * 60)

    print("\n[1/4] 下载ESG报告...")
    cmd_download()

    print("\n[2/4] 预处理PDF...")
    cmd_preprocess()

    print("\n[3/4] 大模型提取指标...")
    cmd_extract()

    print("\n[4/4] 校验并导入数据库...")
    cmd_validate()
    cmd_db_import()

    print("\n全流程完成！运行 `python run.py app` 启动可视化应用")


if __name__ == "__main__":
    commands = {
        "download": cmd_download,
        "preprocess": cmd_preprocess,
        "extract": cmd_extract,
        "validate": cmd_validate,
        "db-import": cmd_db_import,
        "analyze": cmd_analyze,
        "app": cmd_app,
        "all": cmd_all,
    }

    if len(sys.argv) < 2:
        print("用法: python run.py [download|preprocess|extract|validate|db-import|analyze|app|all]")
        print("  download   - 下载ESG报告PDF")
        print("  preprocess - 预处理PDF（文本提取+表格识别）")
        print("  extract    - DeepSeek大模型提取指标")
        print("  validate   - 校验提取结果质量")
        print("  db-import  - 导入数据到SQLite数据库")
        print("  analyze    - ESG数据分析与行业洞察")
        print("  app        - 启动Streamlit可视化应用")
        print("  all        - 一键运行全流程")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in commands:
        commands[cmd]()
    else:
        print(f"未知命令: {cmd}")
        print(f"可用命令: {list(commands.keys())}")
        print("运行 python run.py 查看各命令说明")

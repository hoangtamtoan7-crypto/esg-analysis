"""批量提取所有ESG报告 - 使用DeepSeek API"""
import os, sys, json, logging
from pathlib import Path
from datetime import datetime

os.environ["DEEPSEEK_API_KEY"] = "sk-012c1c2546844e2d857d8ef7b1a006e8"

from src.extractor.extractor import ESGExtractor
from src.extractor.config import cost_tracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

extractor = ESGExtractor(api_key=os.environ["DEEPSEEK_API_KEY"])

OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

md_files = sorted(Path("data/extracted").glob("*.md"))
logger.info(f"Found {len(md_files)} markdown files to process")

success = 0
fail = 0

for i, md_path in enumerate(md_files):
    company_name = ""
    report_year = ""
    parts = md_path.stem.split("_")
    if len(parts) >= 2:
        company_name = parts[1]
    if len(parts) >= 3:
        report_year = parts[2]

    logger.info(f"[{i+1}/{len(md_files)}] Extracting: {md_path.name}")

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()

        if len(text.strip()) < 500:
            logger.warning(f"Skipping {md_path.name}: too short ({len(text)} chars)")
            fail += 1
            continue

        result = extractor.extract_from_text(
            text, company_name=company_name, report_year=report_year
        )
        result["source_file"] = md_path.name

        output_path = OUTPUT_DIR / f"{md_path.stem}_result.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        qt_count = len(result.get("quantitative_indicators", []))
        ql_count = len(result.get("qualitative_indicators", []))
        logger.info(f"  -> {qt_count} quantitative, {ql_count} qualitative | {cost_tracker.summary()}")

        success += 1

        if not cost_tracker.can_continue():
            logger.warning("BUDGET LIMIT REACHED!")
            break

    except Exception as e:
        logger.error(f"Failed {md_path.name}: {e}")
        fail += 1

logger.info(f"\n===== DONE =====")
logger.info(f"Success: {success}, Failed: {fail}")
logger.info(cost_tracker.summary())
logger.info(f"Results saved to: {OUTPUT_DIR}")

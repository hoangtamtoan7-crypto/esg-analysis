"""SQLite数据库操作

存储公司信息、报告元数据、ESG指标定义和提取结果。
"""

import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, create_engine, JSON,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "data" / "esg_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    exchange = Column(String(20))
    market = Column(String(20))
    industry = Column(String(50))

    reports = relationship("Report", back_populates="company")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    title = Column(String(300))
    pdf_path = Column(String(500))
    md_path = Column(String(500))
    page_count = Column(Integer)
    extraction_status = Column(String(20), default="pending")  # pending/done/error
    quality_score = Column(Float, default=0.0)
    completeness = Column(Float, default=0.0)

    company = relationship("Company", back_populates="reports")
    values = relationship("ExtractedValue", back_populates="report")
    texts = relationship("ExtractedText", back_populates="report")


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(String(20), primary_key=True)  # E_Q01, S_L01, etc.
    name = Column(String(100), nullable=False)
    name_en = Column(String(200))
    dimension = Column(String(1), nullable=False)  # E/S/G
    indicator_type = Column(String(20), nullable=False)  # quantitative/qualitative
    unit = Column(String(50))
    keywords = Column(JSON)
    description = Column(String(500))


class ExtractedValue(Base):
    __tablename__ = "extracted_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    indicator_id = Column(String(20), ForeignKey("indicators.id"), nullable=False)
    value = Column(Float)
    unit = Column(String(50))
    original_text = Column(Text)
    confidence = Column(String(10))

    report = relationship("Report", back_populates="values")


class ExtractedText(Base):
    __tablename__ = "extracted_texts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    indicator_id = Column(String(20), ForeignKey("indicators.id"), nullable=False)
    status = Column(String(10))  # yes/no/partial
    summary = Column(Text)
    original_text = Column(Text)
    confidence = Column(String(10))

    report = relationship("Report", back_populates="texts")


class Database:
    """ESG数据库管理"""

    def __init__(self, db_path: Optional[str] = None):
        path = db_path or str(DB_PATH)
        self.engine = create_engine(f"sqlite:///{path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"数据库初始化完成: {path}")

    def get_session(self):
        return self.Session()

    def add_company(self, stock_code: str, name: str, **kwargs) -> int:
        """添加公司，返回company_id"""
        with self.Session() as session:
            existing = session.query(Company).filter_by(stock_code=stock_code).first()
            if existing:
                for k, v in kwargs.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
                session.commit()
                return existing.id
            company = Company(stock_code=stock_code, name=name, **kwargs)
            session.add(company)
            session.commit()
            return company.id

    def add_report(self, company_id: int, year: int, **kwargs) -> int:
        """添加报告，返回report_id"""
        with self.Session() as session:
            report = Report(company_id=company_id, year=year, **kwargs)
            session.add(report)
            session.commit()
            return report.id

    def import_indicators(self, indicators: list):
        """导入指标体系"""
        with self.Session() as session:
            for ind in indicators:
                existing = session.query(Indicator).filter_by(id=ind.id).first()
                if not existing:
                    indicator = Indicator(
                        id=ind.id,
                        name=ind.name,
                        name_en=ind.name_en,
                        dimension=ind.dimension,
                        indicator_type=ind.indicator_type,
                        unit=ind.unit,
                        keywords=ind.keywords,
                        description=ind.description,
                    )
                    session.add(indicator)
            session.commit()
            logger.info(f"导入{len(indicators)}个指标")

    def save_extraction_result(self, report_id: int, result: dict):
        """保存提取结果到数据库"""
        with self.Session() as session:
            for item in result.get("quantitative_indicators", []):
                value = ExtractedValue(
                    report_id=report_id,
                    indicator_id=item.get("id", ""),
                    value=item.get("value"),
                    unit=item.get("unit"),
                    original_text=item.get("original_text"),
                    confidence=item.get("confidence"),
                )
                session.add(value)

            for item in result.get("qualitative_indicators", []):
                text = ExtractedText(
                    report_id=report_id,
                    indicator_id=item.get("id", ""),
                    status=item.get("status"),
                    summary=item.get("summary"),
                    original_text=item.get("original_text"),
                    confidence=item.get("confidence"),
                )
                session.add(text)

            validation = result.get("validation", {})
            completeness_data = result.get("completeness", {})
            session.query(Report).filter_by(id=report_id).update({
                "extraction_status": "done",
                "quality_score": validation.get("overall_quality_score", 0),
                "completeness": completeness_data.get("completeness", 0),
            })
            session.commit()

    def get_company_indicator_values(self, stock_code: str, indicator_id: str) -> list:
        """查询某公司某指标的所有历史值"""
        with self.Session() as session:
            company = session.query(Company).filter_by(stock_code=stock_code).first()
            if not company:
                return []

            results = (
                session.query(ExtractedValue, Report.year)
                .join(Report)
                .filter(
                    Report.company_id == company.id,
                    ExtractedValue.indicator_id == indicator_id,
                )
                .order_by(Report.year.desc())
                .all()
            )
            return [{"year": r.year, "value": v.value, "unit": v.unit} for v, r in results]

    def get_all_companies_summary(self) -> list:
        """获取所有公司的提取摘要"""
        with self.Session() as session:
            reports = session.query(Report).all()
            return [
                {
                    "id": r.id,
                    "company_id": r.company_id,
                    "year": r.year,
                    "status": r.extraction_status,
                }
                for r in reports
            ]

    def get_statistics(self) -> dict:
        """获取整体统计信息"""
        with self.Session() as session:
            company_count = session.query(Company).count()
            report_count = session.query(Report).count()
            done_count = session.query(Report).filter_by(extraction_status="done").count()
            value_count = session.query(ExtractedValue).count()
            text_count = session.query(ExtractedText).count()

            return {
                "companies": company_count,
                "reports": report_count,
                "reports_done": done_count,
                "extracted_values": value_count,
                "extracted_texts": text_count,
            }

    def get_industry_stats(self) -> list:
        """按行业统计提取结果"""
        with self.Session() as session:
            from sqlalchemy import func
            results = (
                session.query(
                    Company.industry,
                    func.count(Company.id).label("company_count"),
                    func.count(Report.id).label("report_count"),
                )
                .join(Report, Report.company_id == Company.id)
                .filter(Report.extraction_status == "done")
                .group_by(Company.industry)
                .order_by(func.count(Report.id).desc())
                .all()
            )
            return [
                {"industry": r.industry or "未知", "companies": r.company_count, "reports": r.report_count}
                for r in results
            ]


def import_results_from_json(db: Optional[Database] = None) -> dict:
    """将data/output/下的所有_result.json导入数据库

    Returns:
        {"companies": N, "reports": N, "values": N, "texts": N, "errors": [...]}
    """
    import json as json_lib

    from src.extractor.indicators import ALL_INDICATORS

    if db is None:
        db = Database()

    # 先导入指标定义
    db.import_indicators(ALL_INDICATORS)
    logger.info(f"已导入{len(ALL_INDICATORS)}个指标定义")

    output_dir = BASE_DIR / "data" / "output"
    json_files = sorted(output_dir.glob("*_result.json"))
    stats = {"companies": 0, "reports": 0, "values": 0, "texts": 0, "errors": []}

    # 使用单一session处理所有导入
    session = db.get_session()
    try:
        for json_path in json_files:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    result = json_lib.load(f)

                company_name = result.get("company_name", "")
                report_year = result.get("report_year", "")
                source_file = result.get("source_file", json_path.name)

                if not company_name:
                    stats["errors"].append(f"{json_path.name}: 缺少公司名称")
                    continue

                parts = json_path.stem.replace("_result", "").split("_")
                stock_code = parts[0] if parts else ""

                # 查找或创建公司
                company = session.query(Company).filter_by(stock_code=stock_code).first()
                if not company:
                    company = Company(stock_code=stock_code, name=company_name)
                    session.add(company)
                    session.flush()
                    stats["companies"] += 1

                # 创建报告
                year = int(report_year) if report_year and report_year.isdigit() else 0
                validation = result.get("validation", {})
                completeness_data = result.get("completeness", {})
                report = Report(
                    company_id=company.id,
                    year=year,
                    md_path=str(source_file),
                    pdf_path=f"data/pdfs/{parts[0]}_{company_name}_{year}.pdf",
                    extraction_status="done",
                    quality_score=validation.get("overall_quality_score", 0),
                    completeness=completeness_data.get("completeness", 0),
                )
                session.add(report)
                session.flush()
                stats["reports"] += 1

                # 保存定量指标
                for item in result.get("quantitative_indicators", []):
                    value = ExtractedValue(
                        report_id=report.id,
                        indicator_id=item.get("id", ""),
                        value=item.get("value"),
                        unit=item.get("unit"),
                        original_text=item.get("original_text"),
                        confidence=item.get("confidence"),
                    )
                    session.add(value)
                    stats["values"] += 1

                # 保存定性指标
                for item in result.get("qualitative_indicators", []):
                    text = ExtractedText(
                        report_id=report.id,
                        indicator_id=item.get("id", ""),
                        status=item.get("status"),
                        summary=item.get("summary"),
                        original_text=item.get("original_text"),
                        confidence=item.get("confidence"),
                    )
                    session.add(text)
                    stats["texts"] += 1

            except Exception as e:
                logger.error(f"导入失败 {json_path.name}: {e}")
                stats["errors"].append(f"{json_path.name}: {str(e)}")
                session.rollback()

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"批量导入回滚: {e}")
        stats["errors"].append(f"batch_rollback: {str(e)}")
    finally:
        session.close()

    logger.info(
        f"导入完成: {stats['companies']}公司 | {stats['reports']}报告 | "
        f"{stats['values']}定量值 | {stats['texts']}定性值 | "
        f"{len(stats['errors'])}个错误"
    )
    return stats

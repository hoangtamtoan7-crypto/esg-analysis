"""ESG数据智能提取与分析系统 - Streamlit主应用"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.extractor.indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION

st.set_page_config(
    page_title="ESG数据智能提取与分析系统",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"


def get_db():
    """延迟加载数据库"""
    try:
        from src.utils.db import Database
        db_path = BASE_DIR / "data" / "esg_data.db"
        if db_path.exists():
            return Database(str(db_path))
    except Exception:
        pass
    return None


@st.cache_data
def load_all_results() -> list:
    """加载所有提取结果 — 优先数据库，回退JSON"""
    db = get_db()
    if db:
        try:
            stats = db.get_statistics()
            if stats["reports_done"] > 0:
                return _load_from_database(db)
        except Exception:
            pass

    return _load_from_json()


def _load_from_database(db) -> list:
    """从数据库加载提取结果"""
    results = []
    session = db.get_session()
    try:
        from src.utils.db import Company, Report, ExtractedValue, ExtractedText
        reports = session.query(Report).filter_by(extraction_status="done").all()
        for report in reports:
            result = {
                "company_name": report.company.name if report.company else "",
                "report_year": str(report.year),
                "quantitative_indicators": [],
                "qualitative_indicators": [],
                "validation": {
                    "overall_quality_score": report.quality_score or 0,
                    "quantitative_valid": sum(1 for v in report.values if v.value is not None),
                    "quantitative_count": len(report.values),
                    "qualitative_valid": sum(1 for t in report.texts if t.status),
                    "qualitative_count": len(report.texts),
                    "quantitative_issues": [],
                    "qualitative_issues": [],
                },
                "completeness": {
                    "total_indicators": 52,
                    "extracted": len(set(v.indicator_id for v in report.values) | set(t.indicator_id for t in report.texts)),
                    "missing": 0,
                    "completeness": report.completeness or 0,
                },
            }
            for v in report.values:
                result["quantitative_indicators"].append({
                    "id": v.indicator_id,
                    "name": "",
                    "value": v.value,
                    "unit": v.unit,
                    "original_text": v.original_text,
                    "confidence": v.confidence,
                })
            for t in report.texts:
                result["qualitative_indicators"].append({
                    "id": t.indicator_id,
                    "name": "",
                    "status": t.status,
                    "summary": t.summary,
                    "original_text": t.original_text,
                    "confidence": t.confidence,
                })
            results.append(result)
    finally:
        session.close()
    return results


def _load_from_json() -> list:
    """从JSON文件加载提取结果"""
    results = []
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.glob("*_result.json")):
            with open(f, "r", encoding="utf-8") as fp:
                results.append(json.load(fp))
    return results


def build_dataframe(results: list) -> pd.DataFrame:
    """将提取结果转为DataFrame"""
    rows = []
    for r in results:
        company = r.get("company_name", "")
        year = r.get("report_year", "")
        validation = r.get("validation", {})
        completeness = r.get("completeness", {})
        quality = validation.get("overall_quality_score", 0)
        coverage = completeness.get("completeness", 0)

        for item in r.get("quantitative_indicators", []):
            rows.append({
                "公司": company,
                "年份": year,
                "指标ID": item.get("id"),
                "指标名称": item.get("name"),
                "数值": item.get("value"),
                "单位": item.get("unit"),
                "置信度": item.get("confidence"),
                "类型": "定量",
                "质量分": quality,
                "覆盖度": coverage,
            })
        for item in r.get("qualitative_indicators", []):
            rows.append({
                "公司": company,
                "年份": year,
                "指标ID": item.get("id"),
                "指标名称": item.get("name"),
                "数值": item.get("status"),
                "单位": "",
                "置信度": item.get("confidence"),
                "类型": "定性",
                "质量分": quality,
                "覆盖度": coverage,
            })
    return pd.DataFrame(rows)


# ====== 侧边栏导航 ======
with st.sidebar:
    st.title("ESG分析系统")
    st.markdown("---")
    page = st.radio(
        "导航",
        ["首页概览", "数据质量", "公司详情", "指标对比", "ESG分析", "趋势分析", "AI智能助手", "数据管理"],
    )
    st.markdown("---")

    # 数据库状态
    db = get_db()
    if db:
        try:
            s = db.get_statistics()
            st.caption(f"数据库: {s['companies']}公司 | {s['reports_done']}报告已提取")
        except Exception:
            st.caption("数据库: 未连接")
    else:
        st.caption("数据库: 未初始化（运行 db-import）")

    st.caption("数据要素大赛 · ESG报告智能提取与分析")

# ====== 首页概览 ======
if page == "首页概览":
    st.title("ESG数据智能提取与分析系统")
    st.markdown("基于DeepSeek大模型的上市公司ESG报告自动提取与交互式分析平台")

    results = load_all_results()
    df = build_dataframe(results) if results else pd.DataFrame()

    # KPI行
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("已处理报告", len(results) or "0")
    with col2:
        st.metric("覆盖公司", df["公司"].nunique() if not df.empty else "0")
    with col3:
        st.metric("定量指标数", len([i for i in ALL_INDICATORS if i.indicator_type == "quantitative"]))
    with col4:
        st.metric("定性指标数", len([i for i in ALL_INDICATORS if i.indicator_type == "qualitative"]))
    with col5:
        if not df.empty and "质量分" in df.columns:
            avg_q = df.groupby("公司")["质量分"].mean().mean()
            st.metric("平均质量分", f"{avg_q:.2f}" if avg_q else "N/A")
        else:
            st.metric("平均质量分", "N/A")

    st.markdown("---")

    # 指标体系概览
    st.subheader("指标体系概览（共{}个指标）".format(len(ALL_INDICATORS)))
    col_e, col_s, col_g = st.columns(3)

    for col, dim, dim_name, color in [
        (col_e, "E", "环境 (Environmental)", "#2ecc71"),
        (col_s, "S", "社会 (Social)", "#3498db"),
        (col_g, "G", "治理 (Governance)", "#e74c3c"),
    ]:
        with col:
            st.markdown(f"**{dim_name}**")
            indicators = INDICATORS_BY_DIMENSION.get(dim, [])
            qt_count = sum(1 for i in indicators if i.indicator_type == "quantitative")
            ql_count = sum(1 for i in indicators if i.indicator_type == "qualitative")
            st.caption(f"[定量] {qt_count}  [定性] {ql_count}")
            with st.expander("查看指标列表"):
                for ind in indicators:
                    tag = "[定量]" if ind.indicator_type == "quantitative" else "[定性]"
                    st.caption(f"{tag} [{ind.id}] {ind.name}")

    # 数据预览
    if not df.empty:
        st.markdown("---")
        st.subheader("数据预览（前50行）")
        st.dataframe(df.head(50), use_container_width=True)

    # 行业统计（数据库可用时）
    db = get_db()
    if db:
        try:
            industry_stats = db.get_industry_stats()
            if industry_stats:
                st.markdown("---")
                st.subheader("行业覆盖分布")
                ind_df = pd.DataFrame(industry_stats)
                st.dataframe(ind_df, use_container_width=True)
        except Exception:
            pass

# ====== 数据质量页 ======
elif page == "数据质量":
    st.title("数据质量评估")

    results = load_all_results()
    if not results:
        st.warning("暂无数据，请先运行提取引擎。")
    else:
        # 质量分汇总
        quality_data = []
        for r in results:
            validation = r.get("validation", {})
            completeness = r.get("completeness", {})
            quality_data.append({
                "公司": r.get("company_name", ""),
                "年份": r.get("report_year", ""),
                "质量分": validation.get("overall_quality_score", 0),
                "覆盖度(%)": completeness.get("completeness", 0),
                "定量有效": validation.get("quantitative_valid", 0),
                "定量总数": validation.get("quantitative_count", 0),
                "定性有效": validation.get("qualitative_valid", 0),
                "定性总数": validation.get("qualitative_count", 0),
            })

        qdf = pd.DataFrame(quality_data)
        qdf = qdf.sort_values("质量分", ascending=False)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均质量分", f"{qdf['质量分'].mean():.3f}" if not qdf.empty else "N/A")
        with col2:
            st.metric("平均覆盖度", f"{qdf['覆盖度(%)'].mean():.1f}%" if not qdf.empty else "N/A")
        with col3:
            high_q = (qdf["质量分"] > 0.5).sum() if not qdf.empty else 0
            st.metric("高质量报告(>0.5)", high_q)

        st.markdown("---")
        st.subheader("各报告质量明细")
        st.dataframe(qdf, use_container_width=True, hide_index=True)

        # 质量分布图
        if not qdf.empty:
            st.markdown("---")
            st.subheader("质量分布")
            try:
                import plotly.express as px
                fig = px.histogram(qdf, x="质量分", nbins=20, title="报告质量分分布")
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.bar_chart(qdf.set_index("公司")["质量分"])

        # 问题详情
        st.markdown("---")
        st.subheader("校验问题详情")
        selected_company = st.selectbox("选择公司查看问题", qdf["公司"].tolist())
        company_result = next(
            (r for r in results if r.get("company_name") == selected_company), None
        )
        if company_result:
            validation = company_result.get("validation", {})
            qt_issues = validation.get("quantitative_issues", [])
            ql_issues = validation.get("qualitative_issues", [])

            if qt_issues:
                st.markdown("**定量指标问题:**")
                st.dataframe(pd.DataFrame(qt_issues), use_container_width=True)
            else:
                st.success("定量指标无不合理值")

            if ql_issues:
                st.markdown("**定性指标问题:**")
                st.dataframe(pd.DataFrame(ql_issues), use_container_width=True)
            else:
                st.success("定性指标无问题")

            completeness = company_result.get("completeness", {})
            missing = completeness.get("missing_list", [])
            if missing:
                st.markdown("**未覆盖的指标:**")
                st.dataframe(pd.DataFrame(missing), use_container_width=True)

# ====== 公司详情页 ======
elif page == "公司详情":
    st.title("公司ESG详情查询")

    results = load_all_results()
    if not results:
        st.warning("暂无数据，请先运行提取引擎。")
    else:
        companies = sorted(set(r.get("company_name", "") for r in results))
        selected = st.selectbox("选择公司", companies)

        company_result = next(
            (r for r in results if r.get("company_name") == selected), None
        )
        if company_result:
            year = company_result.get("report_year", "")
            validation = company_result.get("validation", {})
            completeness = company_result.get("completeness", {})

            st.subheader(f"{selected} — {year}年度ESG报告")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("质量分", f"{validation.get('overall_quality_score', 0):.3f}")
            with col2:
                st.metric("指标覆盖度", f"{completeness.get('completeness', 0)}%")
            with col3:
                qt = validation.get("quantitative_valid", 0)
                ql = validation.get("qualitative_valid", 0)
                st.metric("有效指标", f"{qt}定量 + {ql}定性")

            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["环境 (E)", "社会 (S)", "治理 (G)"])

            for tab, dim in [(tab1, "E"), (tab2, "S"), (tab3, "G")]:
                with tab:
                    dim_indicators = {i.id: i for i in INDICATORS_BY_DIMENSION.get(dim, [])}

                    # 定量指标
                    qt = [
                        item for item in company_result.get("quantitative_indicators", [])
                        if item.get("id") in dim_indicators
                    ]
                    if qt:
                        st.markdown("**定量指标**")
                        qt_data = []
                        for item in qt:
                            ind_def = dim_indicators.get(item.get("id", ""))
                            qt_data.append({
                                "指标": ind_def.name if ind_def else item.get("name", ""),
                                "数值": item.get("value"),
                                "单位": item.get("unit"),
                                "置信度": item.get("confidence", ""),
                                "原文": (item.get("original_text") or "")[:100],
                            })
                        st.dataframe(pd.DataFrame(qt_data), use_container_width=True)
                    else:
                        st.caption("暂无定量指标数据")

                    # 定性指标
                    ql = [
                        item for item in company_result.get("qualitative_indicators", [])
                        if item.get("id") in dim_indicators
                    ]
                    if ql:
                        st.markdown("**定性指标**")
                        for item in ql:
                            status_label = {"yes": "[是]", "no": "[否]", "partial": "[部分]"}.get(
                                item.get("status"), "[未知]"
                            )
                            ind_def = dim_indicators.get(item.get("id", ""))
                            label = ind_def.name if ind_def else item.get("name", "")
                            with st.expander(f"{status_label} {label}"):
                                st.write(item.get("summary", "无描述"))
                                if item.get("original_text"):
                                    st.caption(f"原文: {item['original_text'][:200]}")
                    else:
                        st.caption("暂无定性指标数据")

# ====== 指标对比页 ======
elif page == "指标对比":
    st.title("多公司ESG指标对比")

    results = load_all_results()
    if not results:
        st.warning("暂无数据，请先运行提取引擎。")
    else:
        df = build_dataframe(results)

        # 维度筛选
        dim_filter = st.radio("筛选维度", ["全部", "E-环境", "S-社会", "G-治理"], horizontal=True)
        dim_map = {"E-环境": "E", "S-社会": "S", "G-治理": "G"}
        if dim_filter != "全部":
            dim_ids = {i.id for i in INDICATORS_BY_DIMENSION.get(dim_map[dim_filter], [])}
            df = df[df["指标ID"].isin(dim_ids)] if not df.empty else df

        indicator_names = sorted(df["指标名称"].unique()) if not df.empty else []
        selected_indicator = st.selectbox("选择对比指标", indicator_names)

        indicator_data = df[df["指标名称"] == selected_indicator] if not df.empty else pd.DataFrame()

        if not indicator_data.empty:
            st.subheader(f"{selected_indicator} — 各公司对比")

            col1, col2 = st.columns([3, 2])
            with col1:
                st.dataframe(
                    indicator_data[["公司", "年份", "数值", "单位", "置信度"]],
                    use_container_width=True,
                    hide_index=True,
                )
            with col2:
                numeric_data = indicator_data[
                    indicator_data["数值"].apply(lambda x: isinstance(x, (int, float)))
                ]
                if not numeric_data.empty:
                    try:
                        import plotly.express as px
                        fig = px.bar(
                            numeric_data,
                            x="公司", y="数值",
                            title="各公司对比",
                            labels={"数值": selected_indicator},
                            color="公司",
                        )
                        fig.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        st.bar_chart(numeric_data.set_index("公司")["数值"])

                # 定性指标展示
                qualitative_data = indicator_data[
                    ~indicator_data["数值"].apply(lambda x: isinstance(x, (int, float)))
                ]
                if not qualitative_data.empty:
                    st.markdown("**定性指标状态:**")
                    for _, row in qualitative_data.iterrows():
                        status = row["数值"]
                        label = {"yes": "[是]", "no": "[否]", "partial": "[部分]"}.get(status, "[未知]")
                        st.caption(f"{label} {row['公司']}: {status}")

# ====== ESG分析页 ======
elif page == "ESG分析":
    st.title("ESG综合分析")

    try:
        from src.analyzer import load_clean_data, compute_esg_scores, industry_analysis, generate_insights

        with st.spinner("计算ESG评分..."):
            df = load_clean_data()
            scores = compute_esg_scores(df)
            industries = industry_analysis(df)
            insights = generate_insights(df)

        # ESG排名
        st.subheader("ESG综合排名 TOP20")
        col1, col2 = st.columns([5, 4])
        with col1:
            st.dataframe(scores.head(20), use_container_width=True, hide_index=True)
        with col2:
            if not scores.empty:
                try:
                    import plotly.graph_objects as go
                    top10 = scores.head(10).iloc[::-1]
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=top10["公司"], x=top10["ESG综合"],
                        orientation="h",
                        marker=dict(
                            color=top10["ESG综合"],
                            colorscale="blugrn",
                            showscale=True,
                            colorbar=dict(title="得分", thickness=12, len=0.5),
                        ),
                        text=top10["ESG综合"].apply(lambda v: f"{v:.3f}"),
                        textposition="outside",
                        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
                    ))
                    fig.update_layout(
                        title=dict(text="ESG综合得分 TOP10", font=dict(size=14)),
                        height=400, margin=dict(l=10, r=10, t=40, b=10),
                        xaxis=dict(range=[0, 1.15], title="ESG综合得分"),
                        yaxis=dict(title=""),
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.bar_chart(top10.set_index("公司")["ESG综合"])

        # ESG维度分布
        st.markdown("---")
        st.subheader("E/S/G 维度得分分布")

        dim_configs = [
            ("E_得分", "环境 (E)", "#2e7d32"),
            ("S_得分", "社会 (S)", "#1565c0"),
            ("G_得分", "治理 (G)", "#e65100"),
        ]

        for dim, label, accent in dim_configs:
            avg = scores[dim].mean()
            st.metric(f"{label} 均值", f"{avg:.3f}")

            try:
                import plotly.graph_objects as go
                data = scores[dim].dropna()
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=data,
                    nbinsx=18,
                    marker=dict(
                        color=accent,
                        opacity=0.75,
                        line=dict(color="white", width=1),
                    ),
                    hovertemplate="得分区间: %{x:.2f}<br>公司数: %{y}<extra></extra>",
                ))
                fig.add_vline(
                    x=avg, line_dash="dash", line_color="#d32f2f",
                    line_width=2, annotation_text=f"均值 {avg:.3f}",
                    annotation_position="top right",
                    annotation_font=dict(color="#d32f2f", size=12),
                )
                fig.update_layout(
                    title=dict(text=f"{label}得分分布", font=dict(size=14)),
                    height=320, margin=dict(l=10, r=10, t=40, b=10),
                    xaxis=dict(title="得分", range=[0, 1.05]),
                    yaxis=dict(title="公司数量"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    bargap=0.05,
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass
            st.markdown("<br style='line-height:2rem;'>", unsafe_allow_html=True)

        # 行业对比
        st.markdown("---")
        st.subheader("行业ESG对比")
        if not industries.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.dataframe(industries, use_container_width=True, hide_index=True)
            with col_b:
                ind_valid = industries.dropna(subset=["平均碳排放(吨)"])
                if not ind_valid.empty:
                    try:
                        import plotly.graph_objects as go
                        ind_valid = ind_valid.sort_values("平均碳排放(吨)", ascending=True)
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            y=ind_valid["行业"], x=ind_valid["平均碳排放(吨)"],
                            orientation="h",
                            marker=dict(
                                color=ind_valid["平均碳排放(吨)"],
                                colorscale="reds",
                                showscale=True,
                                colorbar=dict(title="吨", thickness=12, len=0.5),
                            ),
                            text=ind_valid["平均碳排放(吨)"].apply(lambda v: f"{v:,.0f}"),
                            textposition="outside",
                            hovertemplate="%{y}: %{x:,.0f} 吨<extra></extra>",
                        ))
                        fig.update_layout(
                            title=dict(text="各行业平均碳排放", font=dict(size=14)),
                            height=max(350, 25 * len(ind_valid)),
                            margin=dict(l=10, r=10, t=40, b=10),
                            plot_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

        # 关键洞察
        st.markdown("---")
        st.subheader("关键数据洞察")
        for ins in insights:
            st.info(f"**[{ins['类别']}]** {ins['洞察']}")

    except Exception as e:
        st.warning(f"分析模块暂不可用: {e}")
        st.info("请运行: python run.py analyze")

# ====== 趋势分析页 ======
elif page == "趋势分析":
    st.title("ESG指标趋势分析")
    st.info("趋势分析需要同一公司多年份数据。随着数据积累，此处将展示指标变化趋势。")

    results = load_all_results()
    if results:
        df = build_dataframe(results)
        years = sorted(df["年份"].unique()) if "年份" in df.columns else []
        st.write(f"当前数据覆盖年份: {', '.join(str(y) for y in years) if years else '暂无'}")

        companies = sorted(df["公司"].unique()) if not df.empty else []
        selected = st.selectbox("选择公司", companies)

        company_data = df[df["公司"] == selected] if not df.empty else pd.DataFrame()
        if not company_data.empty and company_data["年份"].nunique() > 1:
            indicators = sorted(company_data["指标名称"].unique())
            selected_ind = st.selectbox("选择指标", indicators)

            trend = company_data[company_data["指标名称"] == selected_ind]
            st.dataframe(trend, use_container_width=True, hide_index=True)

            numeric_trend = trend[
                trend["数值"].apply(lambda x: isinstance(x, (int, float)))
            ]
            if len(numeric_trend) > 1:
                try:
                    import plotly.express as px
                    fig = px.line(
                        numeric_trend.sort_values("年份"),
                        x="年份", y="数值",
                        title=f"{selected_ind} — {selected} 趋势",
                        markers=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.line_chart(numeric_trend.set_index("年份")["数值"])
        elif not company_data.empty:
            st.warning("该公司仅有单一年份数据，暂无法展示趋势。")

# ====== AI智能助手页 ======
elif page == "AI智能助手":
    from src.app.pages.ai_assistant import render_ai_assistant_page
    render_ai_assistant_page()

# ====== 数据管理页 ======
elif page == "数据管理":
    st.title("数据管理")

    tab1, tab2, tab3 = st.tabs(["数据导入", "数据导出", "数据库状态"])

    with tab1:
        st.subheader("运行数据提取流水线")
        st.markdown("""
        | 步骤 | 命令 | 说明 |
        |------|------|------|
        | 1. 下载 | `python run.py download` | 从巨潮资讯网下载ESG报告PDF |
        | 2. 预处理 | `python run.py preprocess` | PDF文本+表格提取为Markdown |
        | 3. 提取 | `python run.py extract` | DeepSeek大模型提取ESG指标 |
        | 4. 校验 | `python run.py validate` | 校验提取结果质量 |
        | 5. 入库 | `python run.py db-import` | 导入SQLite数据库 |
        | 6. 可视化 | `python run.py app` | 启动本应用 |
        """)

    with tab2:
        st.subheader("导出数据")
        results = load_all_results()
        if results:
            df = build_dataframe(results)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("导出CSV（含BOM，Excel可直接打开）", csv, "esg_extracted_data.csv", "text/csv")

            json_str = json.dumps(results, ensure_ascii=False, indent=2)
            st.download_button("导出完整JSON", json_str, "esg_extracted_data.json", "application/json")

            # 仅定量数据导出
            qt_df = df[df["类型"] == "定量"] if not df.empty else pd.DataFrame()
            if not qt_df.empty:
                qt_csv = qt_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("仅导出定量指标CSV", qt_csv, "esg_quantitative.csv", "text/csv")

    with tab3:
        st.subheader("数据库状态")
        db = get_db()
        if db:
            try:
                s = db.get_statistics()
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("公司数", s["companies"])
                with col2:
                    st.metric("报告数", s["reports"])
                with col3:
                    st.metric("已提取", s["reports_done"])
                with col4:
                    st.metric("指标值", s["extracted_values"] + s["extracted_texts"])

                # 行业统计
                industry_stats = db.get_industry_stats()
                if industry_stats:
                    st.markdown("---")
                    st.subheader("行业分布")
                    st.dataframe(pd.DataFrame(industry_stats), use_container_width=True)
            except Exception as e:
                st.error(f"数据库读取失败: {e}")
        else:
            st.warning("数据库未初始化。请运行: python run.py db-import")
            if BASE_DIR.joinpath("data", "output").exists():
                json_count = len(list(BASE_DIR.joinpath("data", "output").glob("*_result.json")))
                st.info(f"检测到 {json_count} 个JSON提取结果，可导入数据库。")


if __name__ == "__main__":
    st.write("请用 `streamlit run src/app/main.py` 启动应用")

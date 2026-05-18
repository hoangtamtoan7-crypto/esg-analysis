"""ESG AI智能助手 — 自然语言驱动的ESG数据查询与分析"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_ai_assistant_page():
    st.title("🤖 ESG AI智能助手")
    st.markdown("基于DeepSeek大模型的自然语言ESG数据查询与分析 — 直接输入问题即可获取答案与可视化")

    # ---- 初始化 session state ----
    if "agent_initialized" not in st.session_state:
        st.session_state.agent_initialized = False
        st.session_state.agent = None
        st.session_state.adapter = None
        st.session_state.messages = []
        st.session_state.tool_trace = []

    if not st.session_state.agent_initialized:
        _init_agent()

    # ---- 侧边栏 ----
    with st.sidebar:
        st.subheader("💡 示例问题")
        examples = [
            "比亚迪的ESG表现怎么样？",
            "ESG综合得分排名前10的公司",
            "对比美的集团和格力电器的碳排放",
            "金融行业ESG表现如何？",
            "哪些公司在环保投入上最多？",
            "女性员工比例最高的5家公司",
            "平安银行的ESG评分排第几？",
            "科技行业平均研发投入占比多少？",
        ]
        for i, ex in enumerate(examples):
            if st.button(ex, key=f"ex_btn_{i}"):
                st.session_state.user_query = ex
                st.rerun()

        st.markdown("---")
        st.caption("💡 提示：可以直接输入公司名、指标名或自然语言问题进行查询。")

        # 调试模式
        if st.checkbox("🔧 显示调试信息"):
            st.caption(f"工具调用记录: {len(st.session_state.tool_trace)}次")
            if st.session_state.tool_trace:
                for i, (name, args) in enumerate(st.session_state.tool_trace[-5:]):
                    st.text(f"{i+1}. {name}({args})")

        # 数据集概况
        st.markdown("---")
        st.subheader("📊 数据概况")
        if st.session_state.adapter:
            overview = st.session_state.adapter.get_data_overview()
            if "error" not in overview:
                st.caption(f"公司: {overview['公司数']} | 行业: {overview['行业数']}")
                st.caption(f"报告: {overview['报告数']} | 平均质量分: {overview['平均质量分']}")
            else:
                st.caption("暂无数据，请先运行提取流程")

    # ---- 聊天显示区 ----
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tables"):
                for tb in msg["tables"]:
                    if tb.get("title"):
                        st.caption(tb["title"])
                    st.dataframe(tb["data"], use_container_width=True)
            if msg.get("figs"):
                for fig in msg["figs"]:
                    if isinstance(fig, go.Figure):
                        st.plotly_chart(fig, use_container_width=True)

    # ---- 输入框 ----
    user_input = st.chat_input("请输入您的ESG数据问题，例如：比亚迪的ESG表现怎么样？")

    query = user_input or st.session_state.pop("user_query", None)
    if query:
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # 构建对话历史
        chat_history = []
        for m in st.session_state.messages[:-1]:
            chat_history.append({"role": m["role"], "content": m["content"]})

        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("正在分析数据..."):
                if st.session_state.agent:
                    result = st.session_state.agent.query(query, chat_history=chat_history)
                    text = result.get("text", "")
                    tool_calls = result.get("tool_calls_made", [])
                    st.session_state.tool_trace.extend(tool_calls)
                else:
                    text = "⚠️ AI助手未初始化，请设置 `DEEPSEEK_API_KEY` 环境变量后刷新页面。"
                    tool_calls = []

                st.markdown(text)

                # 自动生成可视化
                figs, tables = _auto_visualize(tool_calls, st.session_state.adapter)
                for fig in figs:
                    st.plotly_chart(fig, use_container_width=True)
                for tb in tables:
                    if tb.get("title"):
                        st.caption(tb["title"])
                    st.dataframe(tb["data"], use_container_width=True)

        # 保存消息
        st.session_state.messages.append({
            "role": "assistant",
            "content": text,
            "figs": figs,
            "tables": tables,
        })


def _init_agent():
    """延迟初始化Agent（带缓存）"""
    from dotenv import load_dotenv
    from pathlib import Path
    import os
    # 先加载.env，确保API Key可用
    load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
    if not os.getenv("DEEPSEEK_API_KEY"):
        st.warning("⚠️ 未设置 `DEEPSEEK_API_KEY` 环境变量，AI助手功能不可用。请在项目根目录创建.env文件并设置DEEPSEEK_API_KEY=sk-xxx")
        st.session_state.agent_initialized = True
        return

    try:
        with st.spinner("正在加载ESG数据，首次加载需要几秒..."):
            from src.agent.data_adapter import ESGDataAdapter
            from src.agent.query_engine import ESGQueryAgent

            adapter = ESGDataAdapter()
            agent = ESGQueryAgent(adapter)

            st.session_state.adapter = adapter
            st.session_state.agent = agent
            st.session_state.agent_initialized = True

    except Exception as e:
        st.error(f"初始化失败: {e}")
        st.session_state.agent_initialized = True


def _auto_visualize(tool_calls: list, adapter):
    """根据工具调用自动生成图表和表格"""
    figs = []
    tables = []

    if not tool_calls or not adapter or adapter.df.empty:
        return figs, tables

    tool_names = {tc[0] for tc in tool_calls}

    # ---- 汇总每个工具调用的参数 ----
    tc_data = {}
    for name, args in tool_calls:
        tc_data[name] = args

    # ====== ESG评分 → 排名柱状图 ======
    if "get_esg_scores" in tool_names and not adapter.scores.empty:
        top_n = tc_data.get("get_esg_scores", {}).get("top_n", 10)
        top = adapter.scores.head(top_n).copy()
        if not top.empty:
            top["公司"] = pd.Categorical(top["公司"], categories=top["公司"][::-1], ordered=True)
            fig = px.bar(
                top, x="ESG综合", y="公司", orientation="h",
                title=f"ESG综合得分 TOP{min(top_n, len(top))}",
                color="ESG综合", color_continuous_scale="blues",
                text=top["ESG综合"].apply(lambda x: f"{x:.3f}"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=min(500, 70 + len(top) * 30))
            figs.append(fig)

        # 表格
        display_scores = top[["排名", "公司", "行业", "E_得分", "S_得分", "G_得分", "ESG综合"]].copy()
        tables.append({"data": display_scores.set_index("排名"), "title": "ESG评分排名详情"})

    # ====== 公司数据 → E/S/G维度得分柱状图 ======
    if "get_company_data" in tool_names:
        args = tc_data.get("get_company_data", {})
        company_name = args.get("company_name", "")
        if company_name and company_name in adapter.company_index:
            score_row = adapter.scores[adapter.scores["公司"] == company_name]
            if not score_row.empty:
                fig = go.Figure(data=[go.Bar(
                    x=["环境(E)", "社会(S)", "治理(G)"],
                    y=[score_row["E_得分"].iloc[0],
                       score_row["S_得分"].iloc[0],
                       score_row["G_得分"].iloc[0]],
                    marker_color=["#2ecc71", "#3498db", "#e74c3c"],
                    text=[f"{score_row['E_得分'].iloc[0]:.3f}",
                          f"{score_row['S_得分'].iloc[0]:.3f}",
                          f"{score_row['G_得分'].iloc[0]:.3f}"],
                    textposition="outside",
                )])
                fig.update_layout(
                    title=f"{company_name} E/S/G维度得分",
                    yaxis_range=[0, 1.1],
                    height=350,
                )
                figs.append(fig)

    # ====== 多公司对比 → 分组柱状图 ======
    if "compare_companies" in tool_names:
        args = tc_data.get("compare_companies", {})
        company_names = args.get("company_names", [])
        indicator_kws = args.get("indicator_keywords", [])

        if company_names and adapter.df is not None:
            # 组装对比数据
            compact = []
            if indicator_kws:
                # 用关键词匹配指标
                resolved = []
                for kw in indicator_kws:
                    resolved.extend(adapter._resolve_indicators(kw)[:2])
                resolved = list({r["id"]: r for r in resolved}.values())

                for company in company_names:
                    if company not in adapter.company_index:
                        continue
                    info = adapter.company_index[company]
                    row = {"公司": company}
                    qt_by_id = {item.get("id"): item for item in info["quantitative"]}
                    for r in resolved:
                        item = qt_by_id.get(r["id"])
                        row[r["name"]] = item.get("value") if item else None
                    compact.append(row)
            else:
                # 默认：碳排放、可再生、女性员工、研发
                default_ind = {"E_Q01": "碳排放(吨)", "E_Q06": "可再生(%)",
                               "S_Q02": "女性员工(%)", "S_Q08": "研发占比(%)"}
                for company in company_names:
                    if company not in adapter.company_index:
                        continue
                    info = adapter.company_index[company]
                    row = {"公司": company}
                    qt_by_id = {item.get("id"): item for item in info["quantitative"]}
                    for iid, label in default_ind.items():
                        item = qt_by_id.get(iid)
                        row[label] = item.get("value") if item else None
                    compact.append(row)

            if compact:
                cdf = pd.DataFrame(compact)
                # 对每个数值列生成图表
                value_cols = [c for c in cdf.columns if c != "公司"]
                valid_cols = [c for c in value_cols if cdf[c].notna().sum() > 0]
                if valid_cols:
                    # 只展示有数据的列
                    melted = cdf.melt(id_vars=["公司"], value_vars=valid_cols,
                                      var_name="指标", value_name="数值")
                    melted = melted.dropna(subset=["数值"])
                    if not melted.empty:
                        fig = px.bar(
                            melted, x="公司", y="数值", color="指标", barmode="group",
                            title=f"多公司ESG指标对比",
                        )
                        fig.update_layout(height=400)
                        figs.append(fig)

                    tables.append({"data": cdf, "title": "指标对比明细"})

    # ====== 行业分析 → 行业对比柱状图 ======
    if "get_industry_analysis" in tool_names and not adapter.industries.empty:
        ind_df = adapter.industries.copy()
        if not ind_df.empty:
            # 碳排放
            if "平均碳排放(吨)" in ind_df.columns and ind_df["平均碳排放(吨)"].notna().sum() > 0:
                fig = px.bar(
                    ind_df.dropna(subset=["平均碳排放(吨)"]),
                    x="行业", y="平均碳排放(吨)", color="行业",
                    title="各行业平均碳排放对比",
                )
                fig.update_layout(showlegend=False, height=350)
                figs.append(fig)

            tables.append({"data": ind_df, "title": "行业ESG对比分析"})

    # ====== 趋势 → 折线图 ======
    if "get_trend" in tool_names:
        tc_args = tc_data.get("get_trend", {})
        # trend result 已由工具返回，这里从adapter重新取数据绘图
        company = tc_args.get("company_name", "")
        keyword = tc_args.get("indicator_keyword", "")
        if company and company in adapter.company_index:
            trend = adapter.get_trend(company, keyword)
            trend_data = trend.get("趋势数据", [])
            data_points = [d for d in trend_data if d.get("数值") is not None]
            if len(data_points) >= 2:
                tdf = pd.DataFrame(data_points)
                fig = px.line(
                    tdf.sort_values("年份"),
                    x="年份", y="数值", color="指标", markers=True,
                    title=f"{company} — 指标趋势",
                )
                fig.update_layout(height=350)
                figs.append(fig)

    return figs, tables

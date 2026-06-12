# ESG分析系统 — 项目记忆

## 项目概述
面向数据要素大赛的ESG报告智能提取与分析平台。基于DeepSeek从约110家A股上市公司ESG报告PDF中提取52个指标。

## 技术栈
- 前端: React 19 + TypeScript + Vite + TailwindCSS 4 + ECharts 6 + Zustand + React Router v7 (HashRouter)
- 后端: FastAPI (API) / Streamlit (数据应用)
- AI: DeepSeek Chat API + Function Calling
- 数据: SQLite + JSON, pandas

## 重要约定
- data/pdfs/ 下有大量PDF，不要读取
- GitHub仓库: https://github.com/hoangtamtoan7-crypto/esg-analysis
- 获取GitHub内容优先用git clone/pull，不走网页抓取
- 网站建设方案文档: ESG网站建设方案.md
- 部署方式: 纯静态 → EdgeOne Pages

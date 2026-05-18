# 🌐 ESG智能分析系统

基于DeepSeek大模型的上市公司ESG报告智能提取与联网分析平台。

## 功能

- **本地ESG数据库**：覆盖110+家A股上市公司的52个ESG指标查询与分析
- **联网AI助手**：自动搜索最新ESG政策、新闻、行业动态，并建立持久化知识库
- **交互式可视化**：ESG评分排名、行业对比、趋势分析等图表

## 一键部署到 Hugging Face Spaces

[![Deploy to HF Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/deploy-to-spaces-lg.svg)](https://huggingface.co/new-space)

### 部署步骤

1. 点击上方按钮或访问 [huggingface.co/new-space](https://huggingface.co/new-space)
2. Space SDK 选择 **Streamlit**
3. 将本仓库代码推送到创建的 Space 仓库
4. 在 Space Settings → Secrets 中添加：
   - `DEEPSEEK_API_KEY` = `你的DeepSeek API Key`
5. Space 自动构建并启动，访问 URL 即可使用

## 本地运行

```bash
pip install -r requirements.txt
# 设置环境变量 DEEPSEEK_API_KEY=sk-xxx
streamlit run app.py
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API密钥 |

## 系统架构

```
用户问题 → WebESGAgent (DeepSeek Function Calling)
  ├── knowledge_search → ChromaDB（已爬取知识库）
  ├── web_search → DuckDuckGo（联网搜索）
  ├── web_crawl → 爬取网页 → 自动索引
  └── 8个本地工具（ESG评分、公司对比等）
```

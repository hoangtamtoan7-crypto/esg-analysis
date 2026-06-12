# Claude Code Prompt — ESG数据智能分析平台网站建设

> **给 Claude Code 的完整开发指令**
> 本项目由 WorkBuddy 完成方案设计和代码审查，Claude Code 负责编码执行。
> 请严格按照以下指令逐 Phase 完成开发，禁止跳过任何步骤。

---

## ⚠️ 全局规则 (每条都必须遵守)

### 规则组 A：文件操作约束
- **A1**：禁止删除 `frontend/src/` 目录下任何现有 `.tsx` 或 `.ts` 文件，只能修改或新增。
- **A2**：禁止修改 `package.json` 中已有的依赖版本号，只能新增依赖。
- **A3**：禁止修改 `vite.config.ts` 中已有的配置项，只能新增。
- **A4**：新增文件必须放在 `frontend/src/` 目录下的合理子目录中（组件放 `components/`，页面放 `pages/`，store 放 `stores/`，类型放 `types/`，工具函数放 `utils/`）。
- **A5**：所有新增的 `.tsx` 文件必须使用 TypeScript，禁止使用 `.jsx` 或 `.js`。
- **A6**：不要读取 `data/pdfs/` 目录下的任何文件。

### 规则组 B：代码质量约束
- **B1**：每个组件文件不得超过 300 行。超过则必须拆分为子组件。
- **B2**：每个 `useEffect` 必须有清理函数（如果有订阅/定时器）。
- **B3**：所有异步操作必须有 `try/catch` 错误处理，并在 UI 上展示错误信息。
- **B4**：禁止使用 `any` 类型，必须使用具体类型或 `unknown` + 类型守卫。
- **B5**：所有包含中文的静态文本必须使用中文字符，不得使用英文替代（如按钮文本、标题、提示信息等）。
- **B6**：禁止使用 `dangerouslySetInnerHTML`。
- **B7**：禁止使用 `eval`、`new Function`。

### 规则组 C：样式约束
- **C1**：颜色值必须直接使用十六进制或 TailwindCSS v4 类名，禁止使用 CSS 变量引入颜色。
- **C2**：深色侧边栏背景色：`#001529`，浅色主背景：`#f5f5f5`，白色卡片背景：`#ffffff`。
- **C3**：E 维度（环境）相关元素使用 `#52C41A`（绿色），S 维度（社会）使用 `#1677FF`（蓝色），G 维度（治理）使用 `#FA8C16`（橙色）。
- **C4**：所有容器卡片圆角统一为 `rounded-xl`（12px），卡片阴影统一为 `shadow-sm`。
- **C5**：页面最大内容宽度为 1400px，使用 `max-w-[1400px] mx-auto`。
- **C6**：表格必须有斑马纹（奇偶行交替背景色）、hover 高亮行、表头固定在顶部。
- **C7**：移动端（<768px）卡片布局从多列变为单列，表格横向滚动。

### 规则组 D：交互约束
- **D1**：所有可点击元素必须有 `cursor-pointer` 和 hover 状态变化。
- **D2**：所有数据加载中状态必须使用骨架屏（Skeleton），禁止使用纯文字 "加载中..." 或纯 spinner。
- **D3**：所有空数据状态必须展示居中占位图 + "暂无数据" 文字 + 操作引导按钮。
- **D4**：所有表单输入必须有实时验证，非法输入时立刻显示红色错误提示文字。
- **D5**：页面切换必须保留滚动位置（回到顶部）。
- **D6**：所有数字超过 10,000 的显示必须使用千分位分隔符（如 `12,345,678`）。

### 规则组 E：路由与导航约束
- **E1**：必须使用 HashRouter（已配置），禁止改为 BrowserRouter。
- **E2**：左侧导航菜单在当前路由高亮时，背景色为 `#1677FF`，文字白色，圆角 8px。
- **E3**：侧边栏底部必须显示 "数据要素大赛 · ESG报告智能提取与分析" 文字，字号 12px，颜色 `#ffffff80`。
- **E4**：面包屑导航格式：`首页 > 当前页面名称`，位于主内容区顶部左侧。

### 规则组 F：部署约束
- **F1**：构建产物必须在 `npm run build` 后能独立运行，不依赖任何后端 API（纯静态）。
- **F2**：所有 ESG 数据必须从内嵌 JSON 文件读取，不得发起网络请求获取数据（AI 助手调用 DeepSeek API 除外）。
- **F3**：`npm run build` 必须零报错、零警告。
- **F4**：打包后的 dist 目录总大小不得超过 5MB（不含 node_modules）。

---

## 📂 项目上下文

### 项目路径
- 前端根目录：`C:\Users\13765\OneDrive\Desktop\研究生\数据要素\frontend\`
- 数据源目录：`C:\Users\13765\OneDrive\Desktop\研究生\数据要素\data\output\`（约 490 个 JSON 文件）
- 数据输出目录：`C:\Users\13765\OneDrive\Desktop\研究生\数据要素\data\analysis\`

### 现有技术栈
- React 19.2.6 + TypeScript 6.0
- Vite 8.0
- TailwindCSS 4.3 (via `@tailwindcss/vite` 插件)
- react-router-dom 7.15 (HashRouter 模式)
- Zustand 5.0 (状态管理)
- ECharts 6.1 + echarts-for-react 3.0 (图表)
- Axios 1.16 (HTTP 请求)
- @heroicons/react 2.2 (图标)
- @headlessui/react 2.2 (无头 UI 组件)
- Node.js 22.22.2

### 已完成的页面（9 个，必须保留全部功能）
| 路由 | 页面文件 | 状态 |
|------|---------|------|
| `/` | `src/pages/Home/index.tsx` | ✅ 完整 |
| `/companies` | `src/pages/Companies/index.tsx` | ✅ 完整 |
| `/comparison` | `src/pages/Comparison/index.tsx` | ✅ 完整 |
| `/analysis` | `src/pages/Analysis/index.tsx` | ✅ 完整 |
| `/indicators` | `src/pages/Indicators/index.tsx` | ✅ 完整 |
| `/trends` | `src/pages/Trends/index.tsx` | ✅ 完整 |
| `/policy` | `src/pages/Policy/index.tsx` | ✅ 完整 |
| `/ai-assistant` | `src/pages/AIAssistant/index.tsx` | ✅ 完整 |
| `/reports` | `src/pages/Reports/index.tsx` | ⚠️ 需重构（当前只有 Markdown 下载） |

### 现有 Store
- `src/stores/appStore.ts` — 全局应用状态（overview, stats, loading）
- `src/stores/comparisonStore.ts` — 多公司/多指标对比篮

### 现有组件
- `src/components/Layout/index.tsx` — 侧边栏 + 顶部导航（白色主题）
- `src/components/Charts/` — 空目录，用于放置可复用图表组件
- `src/components/DataTable/` — 空目录，用于放置可复用表格组件
- `src/components/KPICard/` — 空目录，用于放置可复用 KPI 卡片组件

### 现有类型定义（`src/types/index.ts`）
- `Company`, `CompanyDetail`, `ESGScores`, `Indicator`, `IndicatorValue`, `QualitativeValue`
- `ESGScoreRow`, `IndustryRow`, `Insight`, `DimensionDistribution`
- `OverviewData`, `ChatMessage`, `TableData`, `ToolCall`, `DataStats`
- `TrendPoint`, `CompanyTrend`, `IndustryBenchmark`, `CompanyBenchmark`
- `ScreenRequest`, `ComplianceItem`, `FilterMetadata`

---

## 🎯 开发任务：分 4 个 Phase 执行

**重要：按 Phase 顺序依次执行，每个 Phase 完成后报告进度，不要跨 Phase 跳跃。**

---

## Phase 1：UI 升级（一次性完成以下 6 个任务）

### Task 1.1 — 安装依赖
在 `frontend/` 目录下执行：
```bash
npm install antd@5 @ant-design/icons
```
⚠️ 不要安装其他任何新依赖。

### Task 1.2 — 改造 Layout 组件
**文件**：`src/components/Layout/index.tsx`

需要修改的内容：
1. 桌面端侧边栏背景色改为 `#001529`（深蓝黑），宽度保持 240px
2. 桌面端侧边栏内所有文字颜色改为白色系：
   - Logo 文字：白色 (`#ffffff`)，字号 18px，加粗
   - 菜单项未选中：`#ffffffB3`（白色 70% 透明度）
   - 菜单项选中：背景色 `#1677FF`，文字 `#ffffff`，圆角 8px
   - 菜单项 hover：背景色 `#ffffff1A`（白色 10% 透明度）
3. Logo 区域：icon 背景色改为 `#1677FF`，文字 "ESG数据智能平台"
4. 侧边栏底部版权文字改为 `#ffffff80`（白色 50% 透明度）
5. 在主内容区顶部增加面包屑导航：
   - 使用 `useLocation` 获取当前路径
   - 映射规则：`/` → "首页概览"，`/companies` → "公司详情"，`/reports` → "报告生成"，以此类推
   - 格式：`首页 > [当前页]`，灰色小字，位于内容区顶部
6. 移动端侧边栏同步改为深色主题
7. 顶部导航栏（桌面端）：增加搜索输入框占位（暂不实现搜索功能，仅有视觉元素）

### Task 1.3 — 统一主题色系统
**文件**：`src/index.css`

在现有的 `@theme` 块中增加以下颜色定义：
```css
--color-sidebar-bg: #001529;
--color-eco-green: #52C41A;
--color-social-blue: #1677FF;
--color-gov-orange: #FA8C16;
--color-warning-yellow: #FAAD14;
--color-danger-red: #FF4D4F;
--color-bg-page: #f5f5f5;
--color-card-bg: #ffffff;
```

### Task 1.4 — 改造 Home 页
**文件**：`src/pages/Home/index.tsx`

需要增加的改动：
1. 背景色改为 `#f5f5f5`
2. 顶部 KPI 卡片改为 4 列 grid（桌面端），每张卡片：
   - 白色背景，圆角 12px
   - 数值大字加粗（28px, `#1677FF`）
   - 标签小字灰色（14px, `#8c8c8c`）
   - 右下角配迷你趋势 sparkline（用纯 CSS/SVG，数据模拟即可）
   - hover 时上移 4px + 加深阴影
3. 在行业分布饼图旁边，增加"ESG评分分布热力图"——一个用颜色深浅表示各行业平均 ESG 得分的矩阵图
4. 页面标题 "数据概览" 改为 "ESG数据智能平台"，字号 24px，加粗

### Task 1.5 — 改造 Companies 页
**文件**：`src/pages/Companies/index.tsx`

需要增加的改动：
1. 搜索框改为更大的圆角输入框，带搜索图标前缀
2. 公司详情卡片中，ESG 三个维度得分旁边增加迷你进度条（绿色/蓝色/橙色）
3. 在公司详情区增加"报告年份"下拉选择器（当前值取自数据）
4. 定量指标表格增加颜色标注：高值绿色、中值蓝色、低值橙色

### Task 1.6 — 美化 AI 助手页
**文件**：`src/pages/AIAssistant/index.tsx`

需要增加的改动：
1. 聊天气泡增加圆角（用户气泡 16px 右下直角、AI 气泡 16px 左下直角）
2. AI 消息左侧增加圆形头像图标（默认颜色 `#1677FF`，显示 "AI" 文字）
3. 用户消息右侧增加圆形头像图标（默认颜色 `#52C41A`，显示 "U" 文字）
4. 输入框增加发送按钮（蓝色圆形图标按钮）
5. 消息出现时增加淡入动画（CSS transition opacity 0.3s）

---

## Phase 2：报告生成向导（核心功能，完全重写 Reports 页面）

### 设计参照
参照 https://songxichen.com/AQAssess/#/generate/reports 的向导式交互风格。

### Task 2.1 — 创建报告向导 Store
**新建文件**：`src/stores/reportStore.ts`

```typescript
// Zustand store，管理报告生成的完整流程状态
interface ReportState {
  // 当前步骤: 1-4
  currentStep: number;
  setCurrentStep: (step: number) => void;

  // Step 1: 选择范围
  reportType: 'single' | 'industry' | 'multi';  // 单公司 | 行业 | 多公司
  setReportType: (type: 'single' | 'industry' | 'multi') => void;
  selectedCompanies: string[];  // 选中的公司名称
  toggleCompany: (name: string) => void;
  selectedIndustry: string;     // 行业对比时选中的行业
  setSelectedIndustry: (industry: string) => void;
  selectedYears: string[];      // 选中的年份
  toggleYear: (year: string) => void;

  // Step 2: 配置报告
  reportTitle: string;
  setReportTitle: (title: string) => void;
  reportTemplate: 'standard' | 'detailed' | 'investment';  // 模板类型
  setReportTemplate: (template: 'standard' | 'detailed' | 'investment') => void;
  selectedDimensions: ('E' | 'S' | 'G')[];  // 选中的维度
  toggleDimension: (dim: 'E' | 'S' | 'G') => void;
  author: string;
  setAuthor: (author: string) => void;

  // Step 3-4: 结果
  reportData: any | null;  // 生成后的报告数据
  setReportData: (data: any) => void;
  reportLoading: boolean;
  setReportLoading: (loading: boolean) => void;

  // 重置
  reset: () => void;
}
```

### Task 2.2 — 创建 Step 1 组件：选择范围
**新建文件**：`src/pages/Reports/StepScope.tsx`

功能要求：
1. 报告类型选择：3 个卡片单选按钮（单公司报告 / 行业对比 / 多公司对比），选中卡片蓝色边框
2. 公司选择区：
   - 顶部搜索框（输入即搜索，防抖 300ms）
   - 公司列表（checkbox 多选，显示公司名 + 行业标签）
   - 右侧"已选公司"面板（实时显示已选公司数量和名称，支持点击移除）
3. 年份选择：标签式多选（2024、2025、2026），选中蓝色背景
4. 底部：重置按钮（灰色描边）+ 下一步按钮（蓝色实底，至少选 1 家公司才能点击）
5. 如果"行业对比"模式，公司选择区替换为行业下拉选择器

### Task 2.3 — 创建 Step 2 组件：配置报告
**新建文件**：`src/pages/Reports/StepConfig.tsx`

功能要求：
1. 报告标题输入框（默认值：`{年份}年度ESG评估报告`，可修改）
2. 报告模板选择：3 张可视化卡片
   - 📋 标准摘要：E+S+G 评分 + 关键指标摘要
   - 📊 完整报告：全部 52 个指标 + 全维度分析
   - 🎯 投资分析：ESG 评分 + 风险提示 + 行业对比
   - 选中卡片蓝色边框 + 浅蓝背景，未选中灰色边框
3. 指标维度勾选：3 个 checkbox（E-环境、S-社会、G-治理），默认全选，点击展开具体指标列表
4. 编制人输入框 + 日期选择器（默认今天）
5. 底部：上一步 + 下一步按钮

### Task 2.4 — 创建 Step 3 组件：数据汇总
**新建文件**：`src/pages/Reports/StepSummary.tsx`

功能要求：
1. 数据完整性进度条：
   - 总体完整度（百分比 + 进度条）
   - E/S/G 各维度完整度（3 个独立进度条，绿色/蓝色/橙色）
2. 统计信息：覆盖公司数、指标总数、缺失项数量
3. 缺失项列表：表格展示缺少数据的公司和指标（红色高亮行）
4. "自动填充估算值"按钮（可选，点击后对缺失项用行业均值填充，显示 toast 提示填充项数）
5. 底部：上一步 + 生成报告按钮（主按钮，蓝色实底，带 loading 动画）

### Task 2.5 — 创建 Step 4 组件：生成预览
**新建文件**：`src/pages/Reports/StepPreview.tsx`

功能要求：
1. 报告预览区（白色背景，模拟 A4 纸效果，最大宽度 800px 居中）：
   - 报告标题 + 公司名称 + 编制人 + 日期
   - ESG 综合评分排名（水平柱状图，使用 ECharts）
   - E/S/G 维度得分对比（分组柱状图）
   - 关键指标表格（前 10 个重要指标）
   - 行业对比（如果多公司）
2. 底部操作按钮：
   - 重新生成按钮（灰色描边，回到 Step 1）
   - 下载 PDF 按钮（蓝色实底，使用浏览器 window.print() 或 jsPDF）
   - 复制分享链接按钮（复制当前 URL + hash 参数）
3. 下载 PDF 时使用 `@media print` CSS 隐藏侧边栏和按钮

### Task 2.6 — 重写 Reports 主页面
**文件**：`src/pages/Reports/index.tsx`（完全重写现有文件）

功能要求：
1. 顶部显示步骤条（Steps 组件，4 个步骤）：
   - 当前步骤蓝色实心圆 + 蓝色文字
   - 已完成步骤绿色勾 + 灰色文字
   - 未完成步骤灰色空心圆 + 灰色文字
2. 根据 `currentStep` 渲染对应 Step 组件：
   - Step 1 → `<StepScope />`
   - Step 2 → `<StepConfig />`
   - Step 3 → `<StepSummary />`
   - Step 4 → `<StepPreview />`
3. 所有步骤状态通过 `reportStore` 管理
4. 页面标题改为 "ESG报告生成器"

---

## Phase 3：数据打包与构建

### Task 3.1 — 创建数据打包脚本
**新建文件**：`frontend/scripts/build_data.js`

```javascript
// Node.js 脚本：读取 data/output/*.json → 汇总为 public/data_pack.json
// 使用方式：node scripts/build_data.js
// 输出：frontend/public/data_pack.json
```

脚本逻辑：
1. 遍历 `../data/output/` 下所有 `*_result.json` 文件
2. 提取每家公司的：name, industry, year, quality_score, coverage, esg_scores, quantitative_indicators, qualitative_indicators
3. 从 `../data/analysis/esg_scores.csv` 读取 ESG 评分排名数据
4. 从 `../data/analysis/industry_analysis.csv` 读取行业分析数据
5. 汇总为一个 JSON 对象，写入 `frontend/public/data_pack.json`
6. 控制台输出打包后的文件大小（KB）

### Task 3.2 — 修改前端数据加载方式

1. 在 `src/index.tsx` 或首个渲染的组件中，从 `/data_pack.json` 加载数据
2. 创建 `src/utils/dataLoader.ts`：
   ```typescript
   // 加载内嵌数据并存入 appStore
   import type { OverviewData, ESGScoreRow, IndustryRow } from '../types';

   let cachedData: any = null;

   export async function loadData(): Promise<any> {
     if (cachedData) return cachedData;
     const resp = await fetch('/data_pack.json');
     cachedData = await resp.json();
     return cachedData;
   }

   export function getCompanies(): string[] { ... }
   export function getScores(): ESGScoreRow[] { ... }
   export function getIndustries(): IndustryRow[] { ... }
   // ...更多辅助函数
   ```

3. Home 页面改为从 `loadData()` 获取数据（替换原有的 `apiClient` 调用）

### Task 3.3 — 更新 package.json scripts
在 `frontend/package.json` 中添加：
```json
"build:full": "node scripts/build_data.js && npm run build",
"prebuild": "node scripts/build_data.js"
```

---

## Phase 4：打磨与测试

### Task 4.1 — 响应式适配
1. 移动端（<768px）：
   - 侧边栏默认隐藏，汉堡菜单展开
   - 卡片 grid 从 2-4 列变为 1 列
   - 表格横向滚动
   - 报告生成 Step 组件全宽布局
2. 平板端（768px-1024px）：
   - 侧边栏折叠为图标模式（仅显示图标，宽度 64px）
   - 卡片 grid 最多 2 列

### Task 4.2 — 加载与错误处理
1. 创建 `src/components/ErrorBoundary.tsx`：
   - 捕获渲染错误，显示 "页面加载出错" + 错误信息 + 重试按钮
2. 创建 `src/pages/NotFound.tsx`：
   - 404 页面，显示 "页面未找到" + 返回首页链接
3. 在 `App.tsx` 中添加 `path="*"` 路由指向 NotFound
4. 创建 `src/components/DataSkeleton.tsx`：
   - 可复用的骨架屏组件（支持卡片/表格/图表三种骨架模式）

### Task 4.3 — SEO 与 Meta
**修改文件**：`frontend/index.html`
```html
<title>ESG数据智能分析平台 — A股上市公司ESG报告提取与分析</title>
<meta name="description" content="基于AI的ESG报告数据智能提取与分析平台，覆盖中国A股上市公司环境、社会、治理52项关键指标">
<meta name="keywords" content="ESG,环境,社会,治理,A股,上市公司,数据分析,DeepSeek">
```

### Task 4.4 — 最终检查
1. 运行 `npm run build`，确认零报错零警告
2. 运行 `npm run preview`，在浏览器中检查所有 10 个页面（9 个旧 + 报告向导 4 个步骤）
3. 检查报告生成流程完整走通：选择公司 → 配置 → 汇总 → 预览 → 下载
4. 检查移动端响应式效果（Chrome DevTools 设备模拟）
5. 检查 dist/ 目录大小 < 5MB

---

## 📋 验收检查清单

完成所有 Phase 后，逐项检查：

### 功能验收
- [ ] 深色侧边栏正常显示（背景 #001529，菜单高亮 #1677FF）
- [ ] 面包屑导航正确显示当前页面路径
- [ ] Home 页 KPI 卡片有迷你趋势图
- [ ] 报告生成向导 4 步流程完整可用
- [ ] Step 1 公司搜索和多选正常
- [ ] Step 2 模板选择卡片可点击切换
- [ ] Step 3 数据完整度进度条显示正确
- [ ] Step 4 报告预览区显示图表和数据
- [ ] 下载 PDF 功能正常（打印或导出）
- [ ] 复制分享链接可用
- [ ] AI 助手聊天界面美化完成（气泡圆角、头像）
- [ ] 所有原有页面功能未受影响

### 样式验收
- [ ] 桌面端侧边栏 240px，移动端侧边栏可隐藏
- [ ] 所有卡片圆角 12px
- [ ] E/S/G 颜色使用正确的绿色/蓝色/橙色
- [ ] 表格斑马纹
- [ ] 骨架屏加载态替换文字加载态

### 构建验收
- [ ] `npm run build` 零报错零警告
- [ ] dist/ 目录 < 5MB
- [ ] 所有路由页面可正常访问（包括刷新）

---

## 🔧 技术提示

### Ant Design 按需引入
```tsx
// ✅ 正确做法：只在需要的地方引入
import { Steps, Card, Progress, Table, Tag, Button, Select, DatePicker, Input } from 'antd';
import { DownloadOutlined, ShareAltOutlined } from '@ant-design/icons';
```

### ECharts 在报告预览中的使用
```tsx
import ReactECharts from 'echarts-for-react';
// 所有图表配置遵循 C3 颜色规则（E=#52C41A, S=#1677FF, G=#FA8C16）
```

### 响应式断点
```css
/* 移动端 < 768px: sm */
/* 平板 768-1024px: md */
/* 桌面 > 1024px: lg */
```

### 文件编码
所有文件使用 UTF-8 编码 (BOM: false)，换行符 LF。

---

## ⚡ 执行顺序

```text
Phase 1 → Phase 2 → Phase 3 → Phase 4

每个 Phase 内按 Task 编号顺序执行。
每个 Phase 完成后，报告：
  1. 完成了哪些文件/修改
  2. 遇到什么困难
  3. 有哪些文件需要审查
```

**开始执行 Phase 1 Task 1.1。**

# Fin Research Agent

多 Agent 金融研究助手 — **ReAct 推理 → 多源检索 → 多空辩论 → 投资决策**

## 一句话定位

用 AI Agent 替代投研团队 60% 的信息收集工作：一次提问，自动从 5 类数据源收集信息、交叉验证、输出可溯源的多空观点和投资建议。

## 系统架构

```
用户问题: "HBM产能扩张节奏？"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 0: ReAct Agent (推理引擎)                                 │
│  Thought → Action → Observation 循环                             │
│  动态选择 Tool: kb_search / web_search / sentiment / read_doc    │
└─────────────────────────────────────────────────────────────────┘
         │ 收集 30+ 篇真实文档
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Research Report (多源信息整合)                          │
│  按来源分组 → 关键事实提取 → 矛盾标注                             │
│  数据源: 久谦中台 / Substack / AceCampTech / AlphaEngine / Twitter │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: Debate Team (结构化多空辩论)                            │
│  🐂 看多研究员 ⚔️ 🐻 看空研究员 → ⚖️ 研究经理总结                  │
│  输出: 论点 + 证据 + 来源追溯 + 多空比 + 共识/分歧               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3: Decision Agent (投资决策)                               │
│  建议(买入/持有/卖出) + 置信度 + 风险 + 催化剂 + 跟踪指标         │
└─────────────────────────────────────────────────────────────────┘
```

## 核心技术点

| 模块 | 设计要点 |
|------|---------|
| **ReAct Agent** | Thought→Action→Observation 循环，动态 Tool 选择，max_steps=5 防无限循环 |
| **Tool 抽象层** | BaseTool ABC + 4 个具体实现，关键词提取 fallback 解决金融文档检索难题 |
| **多源融合** | 5 类数据源统一接口，两步检索（宽召回 + 精准定位），矛盾自动标注 |
| **辩论机制** | 3-Agent 协作（Bull/Bear/Moderator），量化多空比，共识提取 |
| **Graceful Degradation** | LLM 不可用时自动 fallback 到 mock 推理链 + 真实 Tool 执行 |

## 快速运行

```bash
git clone https://github.com/1458552246-asu/fin-research-agent.git
cd fin-research-agent
pip install -r requirements.txt
streamlit run demo/app.py
```

不配置 `.env` 自动进入 Demo 模式。配置后连接真实知识库和 LLM。

## 项目结构

```
agent/
├── react_agent.py       # ReAct 推理引擎 (Phase 0)
├── tools.py             # Tool 抽象层 (4 个工具)
├── orchestrator.py      # 工作流编排
├── research_team.py     # 多源研究 (Phase 1)
├── debate_team.py       # 多空辩论 (Phase 2)
├── decision_agent.py    # 投资决策 (Phase 3)
├── kb_client.py         # 知识库 API 客户端
├── models.py            # 数据模型
└── config.py            # 配置管理
demo/
└── app.py               # Streamlit UI
```

## 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Streamlit |
| LLM | Claude (Anthropic) |
| 知识库 | 自建 RAG API (5 类数据源) |
| 架构 | ReAct + Multi-Agent Orchestration |
| 部署 | Streamlit + Cloudflare Tunnel |

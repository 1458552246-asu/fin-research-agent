# 技术架构详解

## 1. 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                           用户层                                      │
│                      Streamlit Web UI                                │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         应用层 (Agent)                                │
├──────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  意图识别    │  │  KB路由     │  │ Bull/Bear  │  │  溯源追踪    │  │
│  │  Router     │→│  Manager    │→│  Analyzer  │→│  Tracer     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         数据层                                        │
├───────────┬───────────┬───────────┬───────────┬───────────┬─────────┤
│  久谦中台  │  Alpha    │  Twitter  │  Substack │  AceCamp  │   LLM   │
│  专家访谈  │  Engine   │   推文    │Newsletter │  共享调研  │ Claude  │
└───────────┴───────────┴───────────┴───────────┴───────────┴─────────┘
```

## 2. 核心模块

### 2.1 意图识别 (IntentRouter)

**功能**: 分析用户问题，识别查询意图

**支持的意图类型**:
- `earnings_call`: 业绩会/财报查询
- `expert_interview`: 专家访谈
- `social_media`: 社交媒体/最新动态
- `research_report`: 研报/研究分析
- `company_outlook`: 公司展望分析
- `industry_trend`: 行业趋势
- `data_comparison`: 数据对比/汇总

**实现原理**:
```python
# 关键词匹配 + 权重计分
for intent_name, config in self._patterns.items():
    score = sum(2 for kw in config["keywords"] if kw in query)
    if score > 0:
        scores[intent_name] = score

# 返回得分最高的意图
best_intent = max(scores, key=scores.get)
```

### 2.2 知识库路由 (KB Manager)

**功能**: 根据意图选择最优数据源组合

**路由策略**:
| 意图 | 优先知识库 |
|------|-----------|
| 业绩会 | AlphaEngine → 久谦 → AceCamp |
| 专家访谈 | 久谦 → AceCamp → AlphaEngine |
| 社交媒体 | Twitter → Substack → AceCamp |
| 研报 | AlphaEngine → AceCamp → 久谦 |

### 2.3 Bull/Bear 分析器

**功能**: 从检索结果中提取结构化的多空观点

**处理流程**:
1. 收集所有来源的内容
2. 调用 Claude 进行观点分类
3. 生成结构化输出

**输出结构**:
```python
@dataclass
class BullBearAnalysis:
    query: str                    # 原始问题
    bull_points: List[Viewpoint]  # 看多论点
    bear_points: List[Viewpoint]  # 看空论点
    synthesis: str                # 综合分析
    overall_stance: str           # 总体立场
    key_factors: List[str]        # 关键因素
    sources_used: List[Dict]      # 使用的来源
```

### 2.4 溯源追踪 (SourceTracer)

**功能**: 为每个观点生成可追溯的来源引用

**输出格式**:
```
久谦中台 · 专家访谈 · 2025-03-18《服务器产业链专家访谈》
> Dell在AI服务器市场份额提升明显...
```

## 3. 两步检索流程

### Step 1: 宽检索 (Discovery)

**目的**: 发现最新相关材料，避免遗漏

**Query 构造策略**:
1. 公司名全变体扩展 (Dell → Dell/DELL/dell/戴尔)
2. 加入上下游/风险词
3. 时间约束 (最新/最近/2025)

```python
# 示例
query_a = "Dell OR DELL OR dell OR 戴尔 最新资料 2025"
query_b = "服务器 AI server 供应链 份额 毛利率 Dell 最新 2025"
```

### Step 2: 精准检索 (Answer)

**目的**: 回答用户的具体问题

**Query 构造策略**:
1. 公司名变体 + 问题核心词
2. 更精确的时间约束

```python
query = "Dell OR 戴尔 业绩 展望 收入 利润 2025"
```

## 4. 数据流

```
用户问题: "Dell未来业绩怎么看"
    │
    ▼
┌─────────────────────────────────────┐
│ 1. 意图识别                          │
│    intent = "company_outlook"       │
│    kb_priority = [28, 17, 19]       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. Query 扩展                        │
│    "Dell OR DELL OR dell OR 戴尔"   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. 多源检索                          │
│    AlphaEngine: 业绩说明会纪要       │
│    久谦中台: 服务器专家访谈          │
│    AceCampTech: PC市场分析          │
│    Twitter: Michael Dell 推文       │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 4. Bull/Bear 分析                    │
│    Bull: AI服务器增长、NVIDIA合作    │
│    Bear: PC下滑、毛利率压力         │
│    Stance: 中性偏多                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 5. 结构化输出 + 来源溯源             │
└─────────────────────────────────────┘
```

## 5. 扩展性设计

### 添加新数据源
```python
# 在 config.py 中添加
KB_ID_TO_NAME[29] = "新数据源"

# 在 router.py 中更新路由策略
INTENT_PATTERNS["new_intent"]["kb_priority"] = [29, ...]
```

### 添加新意图类型
```python
# 在 router.py 中添加
INTENT_PATTERNS["new_intent"] = {
    "keywords": ["关键词1", "关键词2"],
    "kb_priority": [17, 19, 28],
    "description": "新意图描述"
}
```

### 自定义 Bull/Bear 分析
```python
# 修改 bull_bear_analyzer.py 中的 system prompt
BULL_BEAR_SYSTEM_PROMPT = """
你的自定义 prompt...
"""
```

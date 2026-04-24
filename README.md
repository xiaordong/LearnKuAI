# LearnKuAI — AI Agent 设计学习项目

## 一、项目目标

从零开始学习 AI Agent 的设计原理与实现，通过构建一个**智能研究助手（Research Agent）**来掌握 Agent 的核心概念、架构模式和工程实践。

最终成果：一个能够自主搜索信息、整理分析、生成结构化报告的 AI Agent。

---

## 二、核心知识点体系

### 2.1 Agent 基础概念

| 概念 | 说明 |
|---|---|
| **Agent** | LLM + 循环 + 工具。LLM 在循环中自主决策调用工具完成任务 |
| **Agent Loop** | Agent 的核心运行机制：思考 → 行动 → 观察 → 循环，直到任务完成 |
| **Tool Use** | Agent 通过调用外部工具（API、文件、数据库等）与真实世界交互 |
| **ACI** | Agent-Computer Interface，工具接口设计，类似 API 设计对软件的重要性 |
| **Context Engineering** | 上下文工程，管理 Agent 能看到的所有信息（系统提示、历史、工具返回值） |

### 2.2 两大核心架构

#### ReAct（Reasoning + Acting）

```
用户提问
  ↓
[Thought] 我需要搜索 X 信息
  ↓
[Action] 调用搜索工具("X")
  ↓
[Observation] 搜索结果：...
  ↓
[Thought] 根据结果，我还需要搜索 Y
  ↓
[Action] 调用搜索工具("Y")
  ↓
[Observation] 搜索结果：...
  ↓
[Thought] 现在信息足够了，可以回答
  ↓
[Final Answer] 综合回答
```

- 边想边做，逐步推进
- 适合简单任务（<= 3 次工具调用）
- **入门首选**

#### Plan-and-Execute（先计划后执行）

```
用户提问
  ↓
[Plan] 制定完整计划：
  Step 1: 搜索 X 的基础信息
  Step 2: 搜索 Y 的最新进展
  Step 3: 对比分析 X 和 Y
  Step 4: 生成总结报告
  ↓
[Execute Step 1] 调用搜索工具 → 得到结果
  ↓
[Execute Step 2] 调用搜索工具 → 得到结果
  ↓
[Re-Plan] 根据已有结果，调整后续计划（可选）
  ↓
[Execute Step 3] 分析对比 → 得到结果
  ↓
[Execute Step 4] 生成最终报告
```

- 先拆解全局计划，再逐步执行
- 适合复杂多步任务，子任务间有依赖关系
- 错误率比 ReAct 低约 70%
- **进阶学习**

### 2.3 Agent 四大核心组件

```
┌──────────────────────────────────────────┐
│                AI Agent                  │
│                                          │
│  ┌──────────┐    ┌──────────────────┐   │
│  │   LLM    │    │    Memory        │   │
│  │ (大脑)    │    │  (记忆系统)       │   │
│  │          │    │                  │   │
│  │ 推理决策  │    │ · 短期：对话上下文 │   │
│  │ 语言理解  │    │ · 长期：持久存储   │   │
│  │ 任务规划  │    │ · 工作：中间状态   │   │
│  └────┬─────┘    └────────┬─────────┘   │
│       │                   │              │
│       ▼                   ▼              │
│  ┌──────────┐    ┌──────────────────┐   │
│  │ Planning │    │    Tools         │   │
│  │ (规划)    │    │  (工具系统)       │   │
│  │          │    │                  │   │
│  │ 任务分解  │    │ · 搜索引擎        │   │
│  │ 步骤编排  │    │ · 文件读写        │   │
│  │ 优先级   │    │ · 数据库查询      │   │
│  └──────────┘    │ · 代码执行        │   │
│                   └──────────────────┘   │
│                                          │
└──────────────────────────────────────────┘
```

#### 组件详解

**1. LLM（大脑）**
- 负责：推理、决策、语言理解、任务规划
- 选型考量：任务复杂度、响应速度、成本
- 原则：简单任务用小模型，复杂任务用大模型

**2. Memory（记忆系统）**
- **短期记忆**：当前对话的上下文，存在 LLM 的 context window 中
- **长期记忆**：跨会话持久化的状态（向量数据库、关系数据库、文件等）
- **工作记忆**：Agent 执行过程中维护的中间状态（scratchpad）
- 核心挑战：context window 有限，需要精心管理

**3. Tools（工具系统）**
- Agent 与外部世界交互的接口
- 工具设计原则：
  - 功能边界清晰，不重叠
  - 命名直观，描述准确
  - 返回值精简但包含足够推理信息
  - 参数 schema 清晰
- 常见工具类型：搜索、文件操作、数据库、代码执行、API 调用

**4. Planning（规划）**
- 将复杂目标分解为可执行子步骤
- 决定工具调用顺序和依赖关系
- 根据中间结果动态调整计划

### 2.4 五大工作流模式（Anthropic 分类）

| # | 模式 | 原理 | 适用场景 |
|---|---|---|---|
| 1 | **Prompt Chaining（提示链）** | 任务拆成顺序步骤，每步 LLM 处理上一步输出 | 先列提纲再写文章；先翻译再校对 |
| 2 | **Routing（路由）** | 分类输入后导向专门处理流程 | 客服分流；简单问题用小模型复杂用大模型 |
| 3 | **Parallelization（并行化）** | 多个 LLM 同时处理，分段或投票 | 内容审核多视角评审；多源信息搜索 |
| 4 | **Orchestrator-Workers（编排者-工人）** | 中央 LLM 动态分解任务分配给工人 LLM | 根据代码库动态决定改哪些文件 |
| 5 | **Evaluator-Optimizer（评估者-优化者）** | 一个生成一个评估，循环迭代 | 文学翻译精炼；复杂搜索任务 |

### 2.5 高级模式

| 模式 | 说明 |
|---|---|
| **Reflection（反思）** | Agent 批判并迭代优化自身输出 |
| **Self-Improving（自我改进）** | 从反馈中学习，持续优化 |
| **Multi-Agent（多代理）** | 多个 Agent 协作完成复杂任务 |
| **Human-in-the-Loop** | 关键节点引入人工审核和干预 |

### 2.6 生产级 Agent 要求

| 领域 | 要求 |
|---|---|
| **错误处理** | 优雅降级，而非崩溃；fail-safe 而非 fail-fast |
| **安全护栏** | 分层防护：策略护栏 + 内容过滤 + 工具执行控制 |
| **可观测性** | 监控、日志、链路追踪 Agent 行为 |
| **停止条件** | 最大迭代次数、超时限制、token 预算 |
| **模型灵活性** | 便于切换模型，无需大规模代码改动 |
| **沙盒测试** | 隔离环境充分测试 |

---

## 三、项目设计 — 智能研究助手

### 3.1 功能规划

```
用户输入研究主题
       ↓
  ┌─────────────────────────────────┐
  │         Research Agent           │
  │                                  │
  │  1. 分析主题，制定搜索计划        │
  │  2. 调用搜索工具收集信息          │
  │  3. 整理、分析、综合信息          │
  │  4. 生成结构化研究报告            │
  │  5. 保存报告到本地文件            │
  │  6. 支持追问和深入探索            │
  └─────────────────────────────────┘
       ↓
  输出结构化研究报告
```

### 3.2 系统架构

```
research_agent/
├── agent/
│   ├── __init__.py
│   ├── core.py          # Agent Loop 核心（阶段1）
│   ├── tools.py         # 工具注册与定义（阶段2）
│   └── memory.py        # 记忆管理（阶段3）
├── tools/
│   ├── __init__.py
│   ├── search.py        # 搜索工具
│   ├── file_io.py       # 文件读写工具
│   └── summarizer.py    # 摘要工具
├── config.py            # 配置管理
├── main.py              # 入口文件
└── README.md            # 本文件
```

### 3.3 工具清单

| 工具 | 功能 | 使用场景 |
|---|---|---|
| `web_search` | 网络搜索 | 搜索研究主题相关信息 |
| `fetch_page` | 抓取网页内容 | 获取搜索结果的详细内容 |
| `save_note` | 保存笔记到文件 | 记录研究发现 |
| `read_note` | 读取已有笔记 | 回顾之前的研究 |
| `list_notes` | 列出所有笔记 | 查看研究历史 |

### 3.4 技术选型

| 项目 | 选择 | 理由 |
|---|---|---|
| 语言 | Python 3.11+ | AI 生态最成熟 |
| LLM | GLM-4.7（智谱，OpenAI SDK 兼容接口） | 中文能力强，通过 OpenAI SDK 调用 |
| 搜索引擎 | duckduckgo-search（ddgs） | 免费、无需 API Key |
| HTTP 请求 | `httpx` | 支持异步，API 简洁 |
| 数据存储 | SQLite | 轻量数据库，无需额外服务，适合学习阶段 |
| 配置管理 | `python-dotenv` + `.env` | 简单的环境变量管理 |

### 3.5 对话流程设计

```
用户: 帮我研究 "Rust vs Go 的性能对比"

Agent Thought: 这是一个比较类研究，我需要分别搜索两方面的信息
Agent Action: web_search("Rust programming language performance benchmarks 2025")
Agent Observation: [搜索结果列表...]

Agent Thought: 找到了一些 Rust 性能数据，现在搜索 Go 的
Agent Action: web_search("Go programming language performance benchmarks 2025")
Agent Observation: [搜索结果列表...]

Agent Thought: 需要深入了解具体的对比数据
Agent Action: fetch_page("https://...")
Agent Observation: [网页内容...]

Agent Thought: 信息足够了，生成报告并保存
Agent Action: save_note("Rust_vs_Go_性能对比", "报告内容...")
Agent Observation: 笔记已保存

Agent Final Answer:
# Rust vs Go 性能对比研究报告
## 1. 概述
...
## 2. 性能基准测试
...
## 3. 内存占用
...
## 4. 结论
...
报告已保存至 notes/Rust_vs_Go_性能对比.md
```

---

## 四、学习阶段详细计划

### 阶段 1：基础骨架 — Agent Loop

**目标：** 用最少的代码实现 Agent 的核心循环

**核心知识点：**
- Agent Loop 的本质：一个 while 循环
- LLM 的 tool_use 机制：模型如何"决定"调用工具
- 消息格式：system / user / assistant / tool_result
- 停止条件：如何判断 Agent 完成了任务

**要回答的问题：**
- Agent Loop 和普通 API 调用有什么区别？
- LLM 是怎么"知道"该调用什么工具的？
- 为什么要用循环？一次调用不行吗？

**产出：** 一个能运行的 ReAct Agent 骨架，可以调用一个假工具

---

### 阶段 2：工具系统 — Tool Use

**目标：** 为 Agent 添加真实可用的工具

**核心知识点：**
- 工具定义 schema：name、description、parameters
- 工具注册机制：如何让 LLM 知道有哪些工具可用
- ACI 设计原则：工具接口设计的最佳实践
- 工具返回值设计：精简但包含足够推理信息
- 工具调用安全性：参数校验、权限控制

**要回答的问题：**
- 一个好的工具描述应该包含什么？
- 工具太多会不会反而降低 Agent 性能？
- 如何处理工具调用失败的情况？

**产出：** 拥有搜索、网页抓取、文件读写工具的 Agent

---

### 阶段 3：记忆系统 — Memory

**目标：** 为 Agent 添加上下文管理和持久化能力

**核心知识点：**
- 短期记忆：对话历史的截断与摘要策略
- 长期记忆：跨会话的数据持久化
- Context Window 管理：token 计数与上下文压缩
- 上下文工程原则：最小化高信号 token

**要回答的问题：**
- 对话太长超出 context window 怎么办？
- 如何在保持关键信息的同时压缩上下文？
- 什么是 "context rot"？如何避免？

**产出：** 支持多轮对话和研究历史记录的 Agent

---

### 阶段 4：规划能力 — Plan-and-Execute

**目标：** 升级到更智能的规划架构

**核心知识点：**
- 任务分解：将复杂目标拆成子任务
- 计划生成：LLM 如何生成结构化计划
- 动态重规划：根据中间结果调整计划
- ReAct 与 Plan-and-Execute 的融合

**要回答的问题：**
- 什么时候该用 Plan-and-Execute 而非 ReAct？
- 计划太死板，中途发现方向错了怎么办？
- 如何平衡"先想清楚"和"边做边调整"？

**产出：** 具备复杂研究任务规划能力的 Agent

---

### 阶段 5：生产增强 — Production Ready

**目标：** 让 Agent 达到可实际使用的质量

**核心知识点：**
- 错误处理与重试策略
- 安全护栏：输入过滤、输出审查、工具权限
- 可观测性：日志、链路追踪
- 成本控制：token 预算、模型选择策略
- 人工介入机制

**要回答的问题：**
- Agent 陷入死循环怎么处理？
- 如何防止 Agent 执行危险操作？
- 如何监控和调试 Agent 的行为？

**产出：** 一个生产级质量的智能研究助手

---

## 五、参考资源

### 官方文档
- [Building Effective AI Agents — Anthropic](https://www.anthropic.com/research/building-effective-agents)
- [Writing Effective Tools for AI Agents — Anthropic](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Effective Context Engineering — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Claude Agent SDK 文档](https://platform.claude.com/docs/en/agent-sdk)

### 架构模式
- [Google Cloud Agent 设计模式](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)
- [Microsoft Azure Agent 设计模式](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [5 大 Agent 设计模式 — MarkTechPost](https://www.marktechpost.com/2025/10/12/5-most-popular-agentic-ai-design-patterns-every-ai-engineer-should-know/)

### 框架参考
- [LangChain / LangGraph](https://github.com/langchain-ai/langgraph) — 复杂生产级流水线
- [CrewAI](https://github.com/crewAIInc/crewAI) — 多 Agent 协作
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) — 轻量级 Agent

---

## 六、学习记录

> 每个阶段完成后在此记录心得和疑问

### 阶段 1：基础骨架
- 状态：✅ 已完成
- 笔记：
  - Agent Loop 的本质就是一个 while 循环：LLM 返回 tool_calls 时继续循环，返回 stop 时结束
  - 消息格式：system → user → assistant(tool_calls) → tool(结果) → assistant(回答)
  - finish_reason 是循环控制的关键字段

### 阶段 2：工具系统
- 状态：✅ 已完成
- 笔记：
  - ACI 设计三原则：描述告诉 LLM 什么时候用、能做什么、返回什么
  - 工具数量控制在 5-8 个最佳
  - DDGS 搜索透传参数（region/timelimit），让 LLM 自行决定使用
  - execute_tool 加 try-except，错误返回给 LLM 而不是崩掉 Agent
  - fetch_page 处理 HTTP 错误（如 403），返回状态码而非抛异常

### 阶段 3：记忆系统
- 状态：✅ 已完成
- 笔记：
  - 会话持久化：SQLite 双表存储（sessions + messages）
  - 多会话支持：启动时可选新建或加载历史会话
  - 上下文压缩：messages 超过 100K 字符时，旧消息交给 LLM 生成摘要替换
  - SDK 对象需通过 model_dump() 转为 dict 才能序列化
  - Context Window 200K tokens，实际控制阈值设为约 50%
  - JSON → SQLite 迁移：追加消息只需 INSERT，不用重写全部数据

### 阶段 4：规划能力
- 状态：✅ 已完成
- 笔记：
  - 从纯 ReAct 升级为 Plan-and-Execute 模式
  - 新增 update_plan / read_plan 工具，Agent 可维护研究计划
  - 不需要改架构，只改系统提示词 + 新增工具
  - 计划存储在 memory/current_plan.md

### 阶段 5：生产增强
- 状态：✅ 已完成
- 笔记：
  - 日志系统：logging 同时输出到控制台和 agent.log，记录 API 耗时、工具调用、错误
  - API 重试：指数退避（1s → 2s → 4s），最多 3 次
  - 安全护栏：工具调用校验层（工具名、必填参数、类型检查、URL 安全校验）
  - SSRF 防护：fetch_page 禁止访问 localhost、私有 IP 段
  - 自愈机制：结构化错误信息（JSON + hint），LLM 读取后自行修正
  - 降级回退：fetch_page 失败时 LLM 自动降级到搜索摘要回答
  - CSS/JS 清理：fetch_page 移除 style/script 块，避免无用信息污染上下文
  - try-finally 保证异常时也保存会话

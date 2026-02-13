# Trivium

**[English](README.md)**

多智能体协作论文写作工作流，以 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 技能（skill）的形式实现。编排 **Claude Code**、**OpenAI Codex CLI** 和 **Google Gemini CLI** 三个 AI 智能体，独立起草、交叉审阅、辩论并达成共识，协作完成学术论文写作。

## 为什么选择 Trivium

AI 辅助审稿在学术出版中正变得越来越普遍。审稿人日常使用大语言模型来评估稿件——检查逻辑连贯性、写作质量和技术准确性。一篇已经通过三大主流 LLM（Claude、GPT、Gemini）独立审查并达成共识的论文，天然符合这些模型的评判标准。Trivium 正是利用了这一点：让可能评审你论文的同一批模型参与写作过程。每个段落由三个智能体独立起草、交叉审阅、迭代修订，直到三方达成共识。其结果是一篇在构建过程中就已通过主流 AI 审稿人质量门槛的稿件。

## 工作流程

```
你的代码仓库
     |
     v
[阶段 0.1: 理解代码] — 三个智能体分析代码 → flow_document.md
     |
     v
[阶段 0.2: 写作规范] — 提供写作规范 → write_paper_skill.md
     |
     v
[阶段 1: 写段落] — 逐段落循环：
     步骤 2：三个智能体独立起草
     步骤 3：Claude 综合三份草稿 → merged_draft.md
     步骤 4：三维审阅
             ├── Claude：研究逻辑审查
             ├── Codex：代码一致性审查
             └── Gemini：写作规范审查
     步骤 5：双轨修订
             轨道 A：内容修正 → revised_A.md
             轨道 B1：学术润色 → revised_B1_polish.md
             轨道 B2：去 AI 痕迹 → revised_B.md
     步骤 6：Codex + Gemini 投票（通过/驳回）
     └── 辩论循环（最多 3 轮） → 达成共识 → 追加到 paper.md
```

## 架构

```
┌─────────────────────────────────────────────────┐
│  SKILL.md（Claude Code 会话 — 编排器）            │
│                                                 │
│  Claude：分析、综合、修订                          │
│     直接通过 Read / Write / Glob 工具执行          │
├─────────────────────────────────────────────────┤
│  paper_workflow.py（外部智能体协调器）              │
│     ThreadPoolExecutor — 并行调用                 │
├──────────────────────┬──────────────────────────┤
│  codex_bridge.py     │  gemini_bridge.py        │
│  Codex CLI 子进程     │  Gemini CLI 子进程        │
└──────────────────────┴──────────────────────────┘
```

- **Claude (SKILL.md)**：在 Claude Code 会话中直接执行分析、综合和修订，无需子进程。
- **paper_workflow.py**：仅负责通过子进程调用 Codex 和 Gemini。接收 prompt，写入文件（避免 Windows 32KB 命令行长度限制），返回 JSON 结果。
- **Bridge 脚本**：轻量封装，调用 CLI 工具（`codex exec`、`gemini`），将流式 JSON 输出归一化为单个 JSON 响应。

## 环境要求

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [OpenAI Codex CLI](https://github.com/openai/codex)
- [Google Gemini CLI](https://github.com/google-gemini/gemini-cli)
- Python 3.10+

## 安装

将项目克隆到 Claude Code 个人技能目录：

```bash
git clone https://github.com/MetaQiu/Trivium.git ~/.claude/skills/trivium
```

> Trivium 是一个 **Claude Code 技能（skill）** — 一种扩展 Claude Code 能力的插件。安装到技能目录后，在所有 Claude Code 会话中自动可用。

如果需要代理（用于 Gemini 调用），编辑 `~/.claude/skills/trivium/config.json`：

```json
{
  "proxy": {
    "enabled": true,
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
  }
}
```

不需要代理则设置 `"enabled": false`。

## 使用方法

安装后，在任意项目中打开 Claude Code，使用自然语言触发：

| 触发词 | 阶段 | 说明 |
|--------|------|------|
| "理解代码" / "分析代码" / "init" | 0.1 | 三个智能体分析源代码，生成 `flow_document.md` |
| "写作规范" / "设置写作规范" | 0.2 | 提供或确认写作规范 |
| "写段落" / "写第X章" / "write" | 1 | 完整的起草-审阅-辩论循环写作一个段落 |
| "查看状态" / "恢复" / "resume" | — | 恢复中断的工作或查看进度 |

### 示例会话

```
你：    理解代码
Claude: 请提供论文工作空间路径
你：    /home/user/paper
Claude: [步骤 1：Claude 分析代码 → code_structure_index.md + claude_code_understanding.md]
Claude: [步骤 2：Codex + Gemini 利用索引并行分析]
Claude: [步骤 3：综合三方分析 → flow_document.md]
Claude: 请审阅 flow_document.md 确认准确性

你：    写段落，第1章第1段，描述系统架构总览
Claude: [三智能体起草 → 综合 → 审阅 → 修订 → 投票]
Claude: 共识达成，已写入 paper.md
```

## 项目结构

```
Trivium/
├── SKILL.md                    # Claude Code 技能入口（编排逻辑）
├── config.json                 # 代理、工作流参数、Bridge 路径
├── scripts/
│   └── paper_workflow.py       # 外部智能体协调器（Codex + Gemini 调用）
├── templates/                  # 10 个 prompt 模板
│   ├── draft_prompt.md         # 起草规则与约束
│   ├── synthesis_prompt.md     # 三稿合并指令
│   ├── review_code_consistency.md      # Codex：代码-文本一致性审查
│   ├── review_skill_compliance.md      # Gemini：写作规范合规审查
│   ├── review_research_soundness.md    # Claude：研究逻辑审查
│   ├── revision_track_a.md             # 内容修正（接受/拒绝/部分采纳）
│   ├── revision_track_b_polish.md      # 学术润色（Gopen & Swan 7 原则）
│   ├── revision_track_b_deai.md        # 去 AI 痕迹（24 种 AI 写作模式检测）
│   ├── vote_prompt.md                  # 最终通过/驳回投票
│   └── structure_guide.md              # 默认写作规范
└── deps/                       # Bridge 脚本（来自 GuDaStudio）
    ├── collaborating-with-codex/
    │   └── scripts/codex_bridge.py
    └── collaborating-with-gemini/
        └── scripts/gemini_bridge.py
```

## 配置项

编辑 `config.json` 自定义配置：

| 键 | 默认值 | 说明 |
|----|--------|------|
| `proxy.enabled` | `true` | 为 Gemini 调用启用代理 |
| `proxy.http` | `http://127.0.0.1:7890` | HTTP 代理地址 |
| `proxy.https` | `http://127.0.0.1:7890` | HTTPS 代理地址 |
| `workflow.max_debate_rounds` | `3` | 每段落最大辩论轮数 |
| `workflow.consensus_mode` | `"strict"` | `"strict"` = 双方都须通过，`"majority"` = 一方通过即可 |
| `workflow.agent_timeout` | `600` | 每次智能体调用的子进程超时（秒） |
| `bridges.codex` | `deps/.../codex_bridge.py` | Codex Bridge 脚本路径 |
| `bridges.gemini` | `deps/.../gemini_bridge.py` | Gemini Bridge 脚本路径 |

## 工作空间布局

运行工作流后，工作空间结构如下：

```
WORKSPACE/
├── code/                                # 待分析的源代码（用户自行放置）
├── foundation/
│   ├── code_structure_index.md          # Claude 生成的代码结构索引（注入给 Codex/Gemini）
│   ├── _prompts/                        # 自动生成的完整 prompt 文件（避免命令行长度限制）
│   │   ├── init_codex.md
│   │   └── init_gemini.md
│   ├── claude_code_understanding.md     # Claude 的代码分析
│   ├── codex_code_understanding.md      # Codex 的代码分析
│   ├── gemini_code_understanding.md     # Gemini 的代码分析
│   ├── flow_document.md                 # 综合后的事实约束文档
│   └── write_paper_skill.md             # 写作规范
├── drafts/
│   └── ch1_p1/                          # 每段落的批次目录
│       ├── claude_draft.md
│       ├── codex_draft.md
│       ├── gemini_draft.md
│       ├── merged_draft.md
│       ├── synthesis_log.md
│       ├── review_round_1/
│       │   ├── code_consistency.json
│       │   ├── skill_compliance.json
│       │   └── research_soundness.json
│       ├── revision_round_1/
│       │   ├── revision_log.md
│       │   ├── revised_A.md
│       │   ├── revised_B1_polish.md
│       │   └── revised_B.md             # 本轮最终修订稿
│       └── verdict_round_1.json
└── paper.md                             # 累积的论文输出
```

## 工作流详解

### 阶段 0.1：理解代码

三个智能体从不同角度分析代码库，分为三个步骤：

**步骤 1 — Claude 直接分析**：Claude 阅读全部源文件，生成两份输出：
- `code_structure_index.md`：结构化的文件索引，列出每个源文件的职责描述、关键类/函数、推荐阅读顺序。**此文件会嵌入到 Codex 和 Gemini 的 prompt 中**，使它们能直接按索引读取文件而无需自行探索目录。
- `claude_code_understanding.md`：Claude 的完整理解文档。

**步骤 2 — Codex + Gemini 并行分析（依赖步骤 1）**：`paper_workflow.py` 读取 `code_structure_index.md` 并注入到两个智能体的 prompt 中，然后并行调用：
- **Codex**：侧重算法和逻辑级细节 → `codex_code_understanding.md`
- **Gemini**：侧重架构和数据流细节 → `gemini_code_understanding.md`

**步骤 3 — Claude 综合三方分析**：读取三份理解文档，解决矛盾（以最具体/准确的描述为准），综合生成 `flow_document.md`，作为后续写作的**事实约束**。论文中的技术描述不得与此文档矛盾。

### 阶段 1：写段落

每个段落经过以下结构化流水线：

1. **独立起草** — 三个智能体在互不可见的情况下各自起草同一段落，产生多元视角。

2. **综合** — Claude 逐句对比三份草稿，从每份中选取最佳表达，合并为连贯段落。

3. **三维审阅** — 三个正交维度的质量检查并行进行：
   - 代码一致性（Codex）：文本是否准确描述了代码？
   - 写作规范合规（Gemini）：是否符合写作规范？
   - 研究逻辑（Claude）：是否存在逻辑错误或术语问题？

4. **双轨修订** — 按顺序处理所有审阅反馈：
   - 轨道 A：内容修正（对每条审阅意见进行接受/拒绝/部分采纳）
   - 轨道 B1：学术润色（Gopen & Swan 7 原则）
   - 轨道 B2：去 AI 痕迹（检测并修正 24 种 AI 写作模式）

5. **投票** — Codex 和 Gemini 投票通过或驳回。`strict` 模式需双方通过；`majority` 模式一方通过即可。若被驳回，循环重复并处理剩余问题。

### 用户干预点

| 节点 | 时机 | 需要的操作 |
|------|------|------------|
| 阶段 0.1 之后 | `flow_document.md` 生成后 | 确认事实准确性 |
| 阶段 0.2 之后 | 写作规范设定后 | 确认或自定义 |
| 最大辩论轮数后 | 3 轮未达成共识 | 接受当前稿件或手动编辑 |

## 常见问题

**找不到 Codex/Gemini 命令**：确保 `codex` 和 `gemini` 在系统 PATH 中。使用 `codex --version` 和 `gemini --version` 验证。

**Gemini 沙箱错误**（`Sandbox image ... is missing or could not be pulled`）：Gemini CLI 的沙箱模式需要拉取 Google Docker 镜像。`gemini_bridge.py` 默认关闭沙箱（`--sandbox` 默认为 `False`）。如需启用，传入 `--sandbox` 参数并确保 Docker 可访问 `us-docker.pkg.dev`。

**Gemini 代理问题**：编辑 `config.json` 设置正确的代理地址。`HTTP_PROXY` 和 `HTTPS_PROXY` 环境变量仅在 Gemini 调用时自动设置。

**Gemini 429 限流**（`No capacity available for model`）：Gemini API 免费额度有速率限制。CLI 会自动重试，通常等待几秒后即可成功。频繁出现时可降低并行调用频率或稍后重试。

**智能体超时**：默认超时 600 秒。大型代码库可在 `config.json` 中增大 `workflow.agent_timeout`。超时的智能体会优雅地返回错误，不会导致工作流崩溃。

**路径解析失败**：如果 Trivium 报告 `NOT_FOUND`，确保项目克隆到 `~/.claude/skills/trivium/`（目录名必须为 `trivium`）。

**智能体输出为空**：如果某个智能体返回空内容，工作流会继续使用其余智能体的输出。检查 stderr 中的 `[warn]` 消息以确定哪个智能体失败。

## 许可证

MIT

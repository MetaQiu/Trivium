# Trivium

Multi-agent collaborative paper writing system. Orchestrates **Claude Code**, **OpenAI Codex CLI**, and **Google Gemini CLI** to independently draft, cross-review, argue, and reach consensus on academic papers.

## How It Works

```
Your Code Repo
     |
     v
[Phase 0.1: 理解代码] — 3 agents analyze code in parallel → flow_document.md
     |
     v
[Phase 0.2: 写作规范] — You provide writing standards → write_paper_skill.md
     |
     v
[Phase 1: 写段落] — Per-paragraph loop:
     Step 2: Three agents draft independently
     Step 3: Claude synthesizes three drafts → merged_draft.md
     Step 4: Three-dimensional review
             ├── Claude: research soundness
             ├── Codex: code consistency
             └── Gemini: skill compliance
     Step 5: Dual-track revision
             Track A: content fix → revised_A.md
             Track B1: academic polish → revised_B1_polish.md
             Track B2: de-AI rewrite → revised_B.md
     Step 6: Codex + Gemini vote (approve/reject)
     └── Debate loop (up to 3 rounds) → consensus → append to paper.md
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  SKILL.md  (Claude Code session — orchestrator) │
│                                                 │
│  Claude: analysis, synthesis, revision          │
│     directly via Read / Write / Glob tools      │
├─────────────────────────────────────────────────┤
│  paper_workflow.py  (external agent coordinator)│
│     ThreadPoolExecutor — parallel calls         │
├──────────────────────┬──────────────────────────┤
│  codex_bridge.py     │  gemini_bridge.py        │
│  Codex CLI subprocess│  Gemini CLI subprocess   │
└──────────────────────┴──────────────────────────┘
```

- **Claude (SKILL.md)**: Directly performs analysis, synthesis, and revision within the Claude Code session. No subprocess needed.
- **paper_workflow.py**: Only handles Codex and Gemini calls via subprocess. Receives prompts, writes them to files (to avoid Windows 32KB command-line limits), and returns JSON results.
- **Bridge scripts**: Thin wrappers that invoke the CLI tools (`codex exec`, `gemini`) and normalize their streaming JSON output into a single JSON response.

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- [OpenAI Codex CLI](https://github.com/openai/codex)
- [Google Gemini CLI](https://github.com/google-gemini/gemini-cli)
- Python 3.10+

## Installation

Clone directly into your Claude Code personal skills directory:

```bash
git clone https://github.com/YOUR_USERNAME/Trivium.git ~/.claude/skills/trivium
```

Then configure your proxy (if needed for Gemini) by editing `~/.claude/skills/trivium/config.json`:

```json
{
  "proxy": {
    "enabled": true,
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
  }
}
```

If you don't need a proxy, set `"enabled": false`.

## Usage

Once installed, open Claude Code in any project and use:

```
/trivium init       — Analyze your codebase with three agents
/trivium            — Then follow phase prompts
```

Or use natural language triggers:

| Trigger | Phase | Description |
|---------|-------|-------------|
| "理解代码" / "分析代码" / "init" | 0.1 | Three agents analyze your source code, produce `flow_document.md` |
| "写作规范" / "设置写作规范" | 0.2 | Provide or confirm your writing standard |
| "写段落" / "写第X章" / "write" | 1 | Write a paragraph with full draft-review-debate loop |
| "查看状态" / "恢复" / "resume" | — | Resume interrupted work or check progress |

### Example Session

```
You:    理解代码
Claude: 请提供代码目录路径和论文工作空间路径
You:    代码在 /home/user/my-project, 工作空间 /home/user/paper
Claude: [analyzes code with 3 agents → produces flow_document.md]
Claude: 请确认 flow_document.md 的准确性

You:    写段落, 第1章第1段, 描述系统架构总览
Claude: [3 agents draft → synthesize → review → revise → vote]
Claude: 共识达成, 已写入 paper.md
```

## Project Structure

```
Trivium/
├── SKILL.md                    # Claude Code Skill entry point (orchestration logic)
├── config.json                 # Proxy, workflow parameters, bridge paths
├── scripts/
│   └── paper_workflow.py       # External agent coordinator (Codex + Gemini calls)
├── templates/                  # 10 prompt templates
│   ├── draft_prompt.md         # Drafting rules and constraints
│   ├── synthesis_prompt.md     # Three-draft merge instructions
│   ├── review_code_consistency.md      # Codex: code ↔ text consistency check
│   ├── review_skill_compliance.md      # Gemini: writing standard compliance check
│   ├── review_research_soundness.md    # Claude: research soundness check
│   ├── revision_track_a.md             # Content fix (accept/reject/partial)
│   ├── revision_track_b_polish.md      # Academic polish (Gopen & Swan 7 principles)
│   ├── revision_track_b_deai.md        # De-AI rewrite (24 AI pattern detection)
│   ├── vote_prompt.md                  # Final approve/reject vote
│   └── structure_guide.md              # Default writing standard
└── deps/                       # Bridge scripts (from GuDaStudio)
    ├── collaborating-with-codex/
    │   └── scripts/codex_bridge.py
    └── collaborating-with-gemini/
        └── scripts/gemini_bridge.py
```

## Configuration

Edit `config.json` to customize:

| Key | Default | Description |
|-----|---------|-------------|
| `proxy.enabled` | `true` | Enable proxy for Gemini calls |
| `proxy.http` | `http://127.0.0.1:7890` | HTTP proxy address |
| `proxy.https` | `http://127.0.0.1:7890` | HTTPS proxy address |
| `workflow.max_debate_rounds` | `3` | Maximum debate rounds per paragraph |
| `workflow.consensus_mode` | `"strict"` | `"strict"` = both must approve, `"majority"` = one suffices |
| `workflow.agent_timeout` | `600` | Subprocess timeout in seconds per agent call |
| `bridges.codex` | `deps/.../codex_bridge.py` | Path to Codex bridge script |
| `bridges.gemini` | `deps/.../gemini_bridge.py` | Path to Gemini bridge script |

## Workspace Layout

After running the workflow, your workspace will look like:

```
WORKSPACE/
├── foundation/
│   ├── claude_code_understanding.md   # Claude's code analysis
│   ├── codex_code_understanding.md    # Codex's code analysis
│   ├── gemini_code_understanding.md   # Gemini's code analysis
│   ├── flow_document.md               # Synthesized ground truth (factual constraint)
│   └── write_paper_skill.md           # Writing standard
├── drafts/
│   └── ch1_p1/                        # Per-paragraph batch directory
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
│       │   └── revised_B.md           # Final revised draft for this round
│       └── verdict_round_1.json
└── paper.md                           # Accumulated paper output
```

## Workflow Details

### Phase 0.1: Code Understanding

Three agents analyze your codebase from different angles:
- **Claude**: Module-level structure and responsibilities (direct tool access)
- **Codex**: Algorithm and logic-level details (via bridge subprocess)
- **Gemini**: Architecture and data-flow level details (via bridge subprocess)

Claude synthesizes all three analyses into `flow_document.md`, which serves as the **factual constraint** for all subsequent writing. No technical claim in the paper may contradict this document.

### Phase 1: Paragraph Writing

Each paragraph goes through a structured pipeline:

1. **Independent Drafting** — All three agents draft the same paragraph without seeing each other's work. This produces diverse perspectives.

2. **Synthesis** — Claude merges the three drafts sentence by sentence, choosing the best expression from each while maintaining coherence.

3. **Three-Dimensional Review** — Three orthogonal quality checks run in parallel:
   - Code Consistency (Codex): Does the text accurately describe the code?
   - Skill Compliance (Gemini): Does it follow the writing standard?
   - Research Soundness (Claude): Are there logic errors or terminology issues?

4. **Dual-Track Revision** — A sequential pipeline processes all review feedback:
   - Track A: Fix content issues (accept/reject each review item)
   - Track B1: Academic polish (Gopen & Swan 7 principles)
   - Track B2: De-AI rewrite (detect and fix 24 AI writing patterns)

5. **Voting** — Codex and Gemini vote approve/reject. In `strict` mode both must approve; in `majority` mode one suffices. If rejected, the loop repeats with remaining issues.

### User Intervention Points

| Point | When | Action Required |
|-------|------|-----------------|
| After Phase 0.1 | `flow_document.md` produced | Confirm factual accuracy |
| After Phase 0.2 | Writing standard set | Confirm or customize |
| After max debate rounds | No consensus after 3 rounds | Accept current draft or provide manual edits |

## Troubleshooting

**Codex/Gemini not found**: Ensure `codex` and `gemini` are in your system PATH. Verify with `codex --version` and `gemini --version`.

**Gemini proxy issues**: Edit `config.json` and set the correct proxy address. The proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) are set automatically for Gemini calls only.

**Agent timeout**: The default timeout is 600 seconds. For large codebases, increase `workflow.agent_timeout` in `config.json`. Timed-out agents return an error gracefully without crashing the workflow.

**Path resolution fails**: If Trivium reports `NOT_FOUND`, ensure the project is cloned to `~/.claude/skills/trivium/` (the directory name must be `trivium`).

**Empty agent output**: If an agent returns empty content, the workflow continues with the remaining agents' output. Check stderr for `[warn]` messages indicating which agent failed.

## License

MIT

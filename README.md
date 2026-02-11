# Trivium

Multi-agent collaborative paper writing system. Orchestrates **Claude Code**, **OpenAI Codex CLI**, and **Google Gemini CLI** to independently draft, cross-review, argue, and reach consensus on academic papers.

## How It Works

```
Your Code Repo
     |
     v
[Stage 0.1: init] — 3 agents analyze code in parallel → flow_document.md
     |
     v
[Stage 0.2] — You provide writing standards → write_paper_skill.md
     |
     v
[Stage 1: write] — Per-paragraph loop:
     Step 2: Three agents draft independently
     Step 3: Claude synthesizes three drafts
     Step 4: Three-dimensional review (code consistency / SKILL compliance / research soundness)
     Step 5: Dual-track revision (content fix → academic polish → de-AI)
     Step 6: Codex + Gemini vote (approve/reject)
     └── Debate loop (up to 3 rounds) → consensus → append to paper.md
```

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

## Usage

Once installed, open Claude Code in any project and use:

```
/trivium init       — Analyze your codebase with three agents
/trivium            — Then follow phase prompts (写作规范, 写段落, 查看状态)
```

Or use natural language triggers:

- **"理解代码"** — Stage 0.1: Three agents analyze your code
- **"写作规范"** — Stage 0.2: Set your writing standard
- **"写段落"** — Stage 1: Write a paragraph with full debate loop
- **"查看状态"** / **"恢复"** — Resume interrupted work

## Project Structure

```
scripts/           # Main orchestrator
templates/         # 10 prompt templates (draft, synthesis, review, revision, vote)
deps/              # Bridge scripts for Codex CLI and Gemini CLI (from GuDaStudio)
config.json        # Agent configuration, proxy, workflow parameters
SKILL.md           # Claude Code Skill definition (entry point)
```

## Configuration

Edit `config.json` to customize:

| Key | Default | Description |
|-----|---------|-------------|
| `proxy.enabled` | `true` | Enable proxy for Gemini calls |
| `proxy.http` | `http://127.0.0.1:7890` | HTTP proxy address |
| `workflow.max_debate_rounds` | `3` | Maximum debate rounds per paragraph |
| `workflow.consensus_mode` | `"strict"` | `"strict"` = both must approve, `"majority"` = one suffices |

## License

MIT

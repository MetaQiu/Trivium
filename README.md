# Trivium

**[中文文档](README_zh.md)**

A multi-agent collaborative paper writing workflow, implemented as a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill. It orchestrates **Claude Code**, **OpenAI Codex CLI**, and **Google Gemini CLI** to independently draft, cross-review, argue, and reach consensus on academic papers.

## Why Trivium

AI-assisted peer review is becoming increasingly common in academic publishing. Reviewers routinely use LLMs to evaluate manuscripts — checking for logical coherence, writing quality, and technical accuracy. A paper that has already been scrutinized and approved by the three leading LLMs (Claude, GPT, Gemini) is inherently aligned with the evaluation criteria these models apply. Trivium exploits this by making the same models that may judge your paper also participate in writing it: each paragraph is independently drafted, cross-reviewed, and iteratively revised until all three agents reach consensus. The result is a manuscript that has, by construction, passed the quality bar of the most widely used AI reviewers.

## How It Works

```
Your Code Repo
     |
     v
[Phase 1: Code Understanding] — 3 agents analyze code → flow_document.md
     |
     v
[Phase 2: Writing Preparation] — You provide writing standard, outline, references
                                    → WORKSPACE/materials/ → foundation/
     |
     v
[Phase 3: Write Paragraph] — Per-paragraph loop:
     Step 2: Three agents draft independently
     Step 3: Claude synthesizes three drafts → merged_draft.md
     Step 4: Unified review + validation
             4a-b: Three agents review independently (same template)
             4c-d: Three agents discuss each issue (accept/reject vote)
             → validated issues (≥2/3 accept → keep)
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
git clone https://github.com/MetaQiu/Trivium.git ~/.claude/skills/trivium
```

> Trivium is a **Claude Code skill** — a plugin that extends Claude Code with domain-specific capabilities. Once installed in the skills directory, it is automatically available in all your Claude Code sessions.

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

Once installed, open Claude Code in any project and use natural language triggers:

| Trigger | Phase | Description |
|---------|-------|-------------|
| "understand code" / "analyze code" / "init" | 1 | Three agents analyze your source code, produce `flow_document.md` |
| "writing standard" / "writing preparation" / "outline" / "references" | 2 | Provide writing standard, paper outline, and reference materials |
| "write paragraph" / "write chapter X" / "write" | 3 | Write a paragraph with full draft-review-debate loop |
| "check status" / "resume" | — | Resume interrupted work or check progress |

### Example Session

```
You:    Analyze my code
Claude: Please provide the paper workspace path
You:    /home/user/paper
Claude: [Step 1: Claude analyzes code → code_structure_index.md + claude_code_understanding.md]
Claude: [Step 2: Codex + Gemini analyze in parallel using the index]
Claude: [Step 3: Synthesizes all three → flow_document.md]
Claude: Please review flow_document.md for accuracy

You:    Write paragraph, chapter 1 paragraph 1, describe system architecture overview
Claude: [3 agents draft → synthesize → review → revise → vote]
Claude: Consensus reached, appended to paper.md
```

## Project Structure

```
Trivium/
├── SKILL.md                    # Claude Code Skill entry point (orchestration logic)
├── config.json                 # Proxy, workflow parameters, bridge paths
├── scripts/
│   └── paper_workflow.py       # External agent coordinator (Codex + Gemini calls)
├── templates/                  # 12 prompt templates
│   ├── draft_prompt.md         # Drafting rules and constraints
│   ├── synthesis_prompt.md     # Three-draft merge instructions
│   ├── review_unified.md              # Unified review (all 3 dimensions, used by all agents)
│   ├── review_validate.md             # Issue validation (accept/reject discussion)
│   ├── review_code_consistency.md      # (legacy) Codex: code-text consistency check
│   ├── review_skill_compliance.md      # (legacy) Gemini: writing standard compliance check
│   ├── review_research_soundness.md    # (legacy) Claude: research soundness check
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
├── code/                                # Source code to analyze (user places code here)
├── materials/                           # Writing preparation materials (user places files here)
│   ├── write_paper_skill.md             # Writing standard (optional)
│   ├── outline.md                       # Paper outline (optional)
│   └── references.md                    # Reference materials (optional)
├── foundation/
│   ├── code_structure_index.md          # Code structure index generated by Claude (fed to Codex/Gemini)
│   ├── _prompts/                        # Auto-generated full prompt files (avoids CLI length limits)
│   │   ├── init_codex.md
│   │   └── init_gemini.md
│   ├── claude_code_understanding.md     # Claude's code analysis
│   ├── codex_code_understanding.md      # Codex's code analysis
│   ├── gemini_code_understanding.md     # Gemini's code analysis
│   ├── flow_document.md                 # Synthesized ground truth (factual constraint)
│   ├── write_paper_skill.md             # Writing standard (copied from materials/)
│   ├── outline.md                       # Paper outline (copied from materials/)
│   └── references.md                    # Reference materials (copied from materials/)
├── drafts/
│   └── ch1_p1/                          # Per-paragraph batch directory
│       ├── claude_draft.md
│       ├── codex_draft.md
│       ├── gemini_draft.md
│       ├── merged_draft.md
│       ├── synthesis_log.md
│       ├── review_round_1/
│       │   ├── claude_review.json     # Claude's unified review
│       │   ├── codex_review.json      # Codex's unified review
│       │   ├── gemini_review.json     # Gemini's unified review
│       │   ├── all_issues.md          # Combined numbered issue list
│       │   ├── claude_validation.json # Claude's accept/reject per issue
│       │   ├── codex_validation.json  # Codex's accept/reject per issue
│       │   ├── gemini_validation.json # Gemini's accept/reject per issue
│       │   └── validated_issues.json  # Issues passing ≥2/3 validation
│       ├── revision_round_1/
│       │   ├── revision_log.md
│       │   ├── revised_A.md
│       │   ├── revised_B1_polish.md
│       │   └── revised_B.md             # Final revised draft for this round
│       └── verdict_round_1.json
└── paper.md                             # Accumulated paper output
```

## Workflow Details

### Phase 1: Code Understanding

Three agents analyze your codebase from different angles in three sequential steps:

**Step 1 — Claude analyzes directly**: Claude reads all source files and produces two outputs:
- `code_structure_index.md`: A structured file map listing every source file with its responsibility, key classes/functions, and recommended reading order. **This file is embedded into Codex and Gemini's prompts**, allowing them to read files directly by index rather than exploring the directory themselves.
- `claude_code_understanding.md`: Claude's comprehensive understanding document.

**Step 2 — Codex + Gemini analyze in parallel (depends on Step 1)**: `paper_workflow.py` reads `code_structure_index.md` and injects it into both agents' prompts, then calls them in parallel:
- **Codex**: Focuses on algorithm and logic-level details → `codex_code_understanding.md`
- **Gemini**: Focuses on architecture and data-flow details → `gemini_code_understanding.md`

**Step 3 — Claude synthesizes all three analyses**: Reads all three understanding documents, resolves contradictions (favoring the most specific/accurate description), and produces `flow_document.md` — the **factual constraint** for all subsequent writing. No technical claim in the paper may contradict this document.

### Phase 2: Writing Preparation

Place your preparation materials in `WORKSPACE/materials/`. All files are optional:

- `write_paper_skill.md` — Your writing standard (style guide, formatting rules, etc.). If not provided, the built-in `structure_guide.md` is used as default.
- `outline.md` — Your paper outline (chapter/section structure, key points per section).
- `references.md` — Reference materials (related papers, useful paragraphs, notes, or any content that helps inform the writing).

Running this phase copies each file from `materials/` to `foundation/`, where it becomes part of the writing context. The outline and reference materials are injected into all drafting and synthesis prompts, so every agent can see the global paper structure and reference materials while writing.

### Phase 3: Paragraph Writing

Each paragraph goes through a structured pipeline:

1. **Independent Drafting** — All three agents draft the same paragraph without seeing each other's work. This produces diverse perspectives.

2. **Synthesis** — Claude merges the three drafts sentence by sentence, choosing the best expression from each while maintaining coherence.

3. **Unified Review with Explicit Validation** — The review step is split into two phases:
   - **Review phase**: All three agents independently review the merged draft using the same unified template covering code consistency, research soundness, and skill compliance.
   - **Validation phase**: All issues from all three reviewers are collected into a numbered list. Each agent then evaluates every issue and votes accept or reject. An issue is only kept if **≥2 out of 3 agents** explicitly accept it. This eliminates false positives through direct discussion rather than fragile sentence matching.

4. **Dual-Track Revision** — A sequential pipeline processes majority-voted review feedback:
   - Track A: Fix content issues (accept/reject each review item)
   - Track B1: Academic polish (Gopen & Swan 7 principles)
   - Track B2: De-AI rewrite (detect and fix 24 AI writing patterns)

5. **Voting** — Codex and Gemini vote approve/reject. In `strict` mode both must approve; in `majority` mode one suffices. If rejected, the loop repeats with remaining issues.

### User Intervention Points

| Point | When | Action Required |
|-------|------|-----------------|
| After Phase 1 | `flow_document.md` produced | Confirm factual accuracy |
| After Phase 2 | Writing preparation loaded | Confirm materials are correct |
| After max debate rounds | No consensus after 3 rounds | Accept current draft or provide manual edits |

## Troubleshooting

**Codex/Gemini not found**: Ensure `codex` and `gemini` are in your system PATH. Verify with `codex --version` and `gemini --version`.

**Gemini sandbox error** (`Sandbox image ... is missing or could not be pulled`): Gemini CLI's sandbox mode requires pulling a Google Docker image. The `gemini_bridge.py` defaults to sandbox disabled (`--sandbox` defaults to `False`). To enable it, pass `--sandbox` and ensure Docker can access `us-docker.pkg.dev`.

**Gemini proxy issues**: Edit `config.json` and set the correct proxy address. The proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) are set automatically for Gemini calls only.

**Gemini 429 rate limit** (`No capacity available for model`): The Gemini API free tier has rate limits. The CLI retries automatically and usually succeeds after a few seconds. If this happens frequently, reduce parallel call frequency or try again later.

**Agent timeout**: The default timeout is 600 seconds. For large codebases, increase `workflow.agent_timeout` in `config.json`. Timed-out agents return an error gracefully without crashing the workflow.

**Path resolution fails**: If Trivium reports `NOT_FOUND`, ensure the project is cloned to `~/.claude/skills/trivium/` (the directory name must be `trivium`).

**Empty agent output**: If an agent returns empty content, the workflow continues with the remaining agents' output. Check stderr for `[warn]` messages indicating which agent failed.

## License

MIT

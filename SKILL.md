---
name: trivium
description: >
  Multi-agent collaborative paper writing. Orchestrates Claude Code, Codex CLI, and Gemini CLI
  to independently draft, cross-review, argue, and reach consensus on academic paper paragraphs.
  Activate when user mentions: 论文写作、写论文、Trivium、理解代码、写作规范、写段落、论文审稿.
user-invocable: true
argument-hint: "[phase]"
allowed-tools: Bash, Read, Write, Glob, AskUserQuestion
---

## Path Resolution

Trivium installation directory: !`python -c "import pathlib,os; candidates=[pathlib.Path.home()/'.claude'/'skills'/'trivium', *[pathlib.Path(p)/'.claude'/'skills'/'trivium' for p in os.environ.get('CLAUDE_ADD_DIRS','').split(os.pathsep) if p]]; print(next((str(c) for c in candidates if (c/'SKILL.md').exists()), 'NOT_FOUND'))"`

The above resolved path is `TRIVIUM_HOME`. All references below use it:
- Script: `TRIVIUM_HOME/scripts/paper_workflow.py`
- Templates: `TRIVIUM_HOME/templates/`

If the path resolved to `NOT_FOUND`, tell the user to check their installation (see README.md).

## Architecture

This skill uses THREE AI agents:
- **Claude (you)**: Analysis, synthesis, revision — executed directly in this session
- **Codex CLI**: Code-focused review and drafting — called via Python script
- **Gemini CLI**: Architecture-focused review and drafting — called via Python script

The Python script `paper_workflow.py` ONLY handles Codex/Gemini calls. You do all Claude work directly using Read/Write/Glob tools.

## Phases

Execute ONLY the phase the user requests. Never skip ahead.

---

### Phase: 理解代码 (Code Understanding)

**Trigger**: User says "理解代码"、"分析代码"、"Stage 0.1"、"init"

**Before running**: Ask user for:
1. `CODE_DIR`: 代码目录路径 (the source code to analyze)
2. `WORKSPACE`: 论文工作空间路径 (where outputs will be saved)

**Execution**:

**Step 1 — You analyze the codebase directly:**
Use Glob and Read tools to explore `CODE_DIR`. Produce a comprehensive understanding document covering:
- System architecture overview
- Core algorithm flow (pseudo-code level)
- Data flow paths
- Key design decisions and rationale
Focus on module-level structure and responsibilities.
Save your analysis to `WORKSPACE/foundation/claude_code_understanding.md`.

**Step 2 — Codex and Gemini analyze in parallel:**
Run in background, no timeout:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py init-external --code-dir "CODE_DIR" --cd "WORKSPACE"
```
This calls Codex (algorithm-level) and Gemini (architecture-level) in parallel.
Wait for it to complete, then verify success from the JSON output.

**Step 3 — You synthesize all three analyses:**
Read these three files:
- `WORKSPACE/foundation/claude_code_understanding.md` (your analysis)
- `WORKSPACE/foundation/codex_code_understanding.md` (Codex's analysis)
- `WORKSPACE/foundation/gemini_code_understanding.md` (Gemini's analysis)

Synthesize them into a single, comprehensive flow document. Resolve contradictions by favoring the most specific/accurate description. Save to `WORKSPACE/foundation/flow_document.md`.

**After**: Tell user to review `flow_document.md` and confirm accuracy before proceeding.

---

### Phase: 写作规范 (Writing Standard)

**Trigger**: User says "写作规范"、"设置写作规范"、"Stage 0.2"

**Before running**: Ask user for:
1. 写作规范文件的路径 (path to their writing standard file)
2. `WORKSPACE`: 论文工作空间路径

**Action**: Copy the user's writing standard file to `WORKSPACE/foundation/write_paper_skill.md`.
This phase does NOT call any script — just copy the file.

If user has no custom standard, inform them the default `TRIVIUM_HOME/templates/structure_guide.md` will be used automatically.

---

### Phase: 写段落 (Write Paragraph)

**Trigger**: User says "写段落"、"写第X章"、"Stage 1"、"write"

**Before running**: Ask user for:
1. `CHAPTER`: 章节号 (integer)
2. `PARAGRAPH`: 段落号 (integer)
3. `PROMPT`: 本段写作要求 (what this paragraph should cover)
4. `WORKSPACE`: 论文工作空间路径

**Pre-check**: Verify `WORKSPACE/foundation/flow_document.md` exists. If not, tell user to run "理解代码" phase first.

Set `BATCH_DIR` = `WORKSPACE/drafts/ch{CHAPTER}_p{PARAGRAPH}`.

#### Step 1: Load Context

Read these files into memory (you will need them throughout):
- `WORKSPACE/foundation/flow_document.md` → this is the FACTUAL CONSTRAINT (ground truth)
- `WORKSPACE/foundation/write_paper_skill.md` (or `TRIVIUM_HOME/templates/structure_guide.md` if not present) → writing standard
- `WORKSPACE/paper.md` → previously written paragraphs (for continuity)

#### Step 2: Independent Drafting (3 agents)

**2a. You draft directly:**
Read `TRIVIUM_HOME/templates/draft_prompt.md` for the drafting rules and constraints.
Following those rules, draft Chapter {CHAPTER} Paragraph {PARAGRAPH} based on the user's PROMPT, the factual constraint, the writing standard, and previous paragraphs.
Save to `BATCH_DIR/claude_draft.md`.

**2b. Codex and Gemini draft in parallel:**
Run in background:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py draft-external --cd "WORKSPACE" --chapter CHAPTER --paragraph PARAGRAPH --instruction "PROMPT"
```
Wait for completion. Results saved to `BATCH_DIR/codex_draft.md` and `BATCH_DIR/gemini_draft.md`.

#### Step 3: Synthesis

Read all three drafts:
- `BATCH_DIR/claude_draft.md`
- `BATCH_DIR/codex_draft.md`
- `BATCH_DIR/gemini_draft.md`

Read `TRIVIUM_HOME/templates/synthesis_prompt.md` for synthesis instructions.
Compare all three drafts sentence by sentence. For each divergence, evaluate factual accuracy (against flow_document), clarity, and academic tone. Select the best expression from each draft and merge into a single coherent paragraph.

Save the merged paragraph to `BATCH_DIR/merged_draft.md`.
Save synthesis notes to `BATCH_DIR/synthesis_log.md`.

#### Steps 4–6: Debate Loop (max 3 rounds)

Set `CURRENT_DRAFT_FILE` = `BATCH_DIR/merged_draft.md`.

For `ROUND` = 1, 2, 3:

##### Step 4: Three-Dimensional Review

**4a. You review for research soundness:**
Read `TRIVIUM_HOME/templates/review_research_soundness.md` for review instructions.
Review `CURRENT_DRAFT_FILE` following those instructions. Focus on: fatal logic contradictions, terminology consistency, severe grammar errors. Use high tolerance threshold — only flag issues that block reader comprehension.
Save your review as JSON to `BATCH_DIR/review_round_{ROUND}/research_soundness.json`.

**4b. Codex and Gemini review in parallel:**
Run in background:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py review-external --cd "WORKSPACE" --batch-dir "BATCH_DIR" --round ROUND --draft-file "CURRENT_DRAFT_FILE"
```
Wait for completion. Read the JSON output for `code_consistency` and `skill_compliance` results.

##### Step 5: Dual-Track Revision

Read all three review results:
- `BATCH_DIR/review_round_{ROUND}/code_consistency.json`
- `BATCH_DIR/review_round_{ROUND}/skill_compliance.json`
- `BATCH_DIR/review_round_{ROUND}/research_soundness.json`

Count total issues. If zero issues, skip revision and go directly to Step 6.

If there are issues:

**Track A — Content Fix:**
Read `TRIVIUM_HOME/templates/revision_track_a.md` for instructions.
Process every issue: ACCEPT (apply fix), REJECT (explain why original is correct), or PARTIALLY ADOPT (apply better fix). Code consistency issues are MANDATORY to fix.
Save revision decisions to `BATCH_DIR/revision_round_{ROUND}/revision_log.md`.
Save revised paragraph to `BATCH_DIR/revision_round_{ROUND}/revised_A.md`.

**Track B1 — Academic Polish:**
Read `TRIVIUM_HOME/templates/revision_track_b_polish.md` for instructions.
Apply Gopen & Swan 7 principles, fix grammar, improve sentence flow.
Save to `BATCH_DIR/revision_round_{ROUND}/revised_B1_polish.md`.

**Track B2 — De-AI:**
Read `TRIVIUM_HOME/templates/revision_track_b_deai.md` for instructions.
Detect and fix AI writing patterns. If the text is already natural, keep it unchanged.
Save to `BATCH_DIR/revision_round_{ROUND}/revised_B.md`.

Update `CURRENT_DRAFT_FILE` = `BATCH_DIR/revision_round_{ROUND}/revised_B.md`.

##### Step 6: Voting

Run in background:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py vote-external --cd "WORKSPACE" --batch-dir "BATCH_DIR" --round ROUND --draft-file "CURRENT_DRAFT_FILE"
```

Read the JSON output. Check:
- `consensus`: true → **CONSENSUS REACHED**. Break out of the loop.
- `consensus`: false → Read `remaining_issues`. If `ROUND` < 3, go back to Step 4 with updated `CURRENT_DRAFT_FILE`. If `ROUND` = 3, proceed to manual decision.

##### After the Loop

- **If consensus reached**: Read `CURRENT_DRAFT_FILE` and append its content to `WORKSPACE/paper.md`. Report success to user.
- **If max rounds exhausted without consensus**: Show the remaining issues to the user. Ask them to decide: accept the current draft as-is, or provide manual edits.

---

### Phase: 恢复/查看状态 (Resume / Check Status)

**Trigger**: User says "查看状态"、"当前进度"、"resume"、"恢复"

**Before running**: Ask user for:
1. `WORKSPACE`: 论文工作空间路径

**Action**: Read `WORKSPACE/paper.md` and report how many paragraphs have been written. List the directories under `WORKSPACE/drafts/` to show which paragraphs have been worked on. For each, check if a `verdict_round_*.json` with consensus exists.

---

## Important Rules

1. **Always run Python scripts in background** with no timeout — external agent calls can be slow.
2. **Proxy**: Gemini calls need proxy. This is handled automatically by `config.json`. If user has proxy issues, tell them to edit `TRIVIUM_HOME/config.json`.
3. **Never skip phases**: If user asks to write paragraphs but `flow_document.md` doesn't exist, remind them to run "理解代码" first.
4. **User intervention points**:
   - After Phase 理解代码: user must confirm `flow_document.md`
   - After Phase 写作规范: user must confirm `write_paper_skill.md`
   - After Phase 写段落: if consensus fails, user decides
5. **Language**: Interact with user in Chinese. Your own drafting/review/revision work should produce English academic text (unless the paper is in Chinese).
6. **Workspace reuse**: If user has been working in a specific workspace during this session, remember it and don't ask again.
7. **Templates are instructions, not prompts**: When told to "read template X for instructions", you should read the template file, understand its rules and constraints, and follow them directly in your work. Do NOT pass the template to any subprocess.

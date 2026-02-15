---
name: trivium
description: >
  Multi-agent collaborative paper writing. Orchestrates Claude Code, Codex CLI, and Gemini CLI
  to independently draft, cross-review, argue, and reach consensus on academic paper paragraphs.
  Activate when user mentions: 论文写作、写论文、Trivium、理解代码、写作规范、写作准备、大纲、参考资料、写段落、论文审稿.
user-invocable: true
argument-hint: "[phase]"
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, mcp__augment-context-engine__codebase-retrieval
---

## Path Resolution

Trivium installation directory: !`python -c "import pathlib,os; candidates=[pathlib.Path.home()/'.claude'/'skills'/'trivium', pathlib.Path.cwd()/'.claude'/'skills'/'trivium', *[pathlib.Path(p)/'.claude'/'skills'/'trivium' for p in os.environ.get('CLAUDE_ADD_DIRS','').split(os.pathsep) if p]]; print(next((str(c) for c in candidates if (c/'SKILL.md').exists()), 'NOT_FOUND'))"`

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

### Phase 1: 理解代码 (Code Understanding)

**Trigger**: User says "理解代码"、"分析代码"、"Stage 1"、"init"

**Before running**: Ask user for:
1. `WORKSPACE`: 论文工作空间路径 (where outputs will be saved)

**Convention**: `CODE_DIR` = `WORKSPACE/code`. The source code to analyze MUST be placed in this directory before running. If `WORKSPACE/code` does not exist, tell the user to copy or symlink their source code there first.

**Execution**:

**Step 1 — You analyze the codebase directly:**
First use Glob to list all source files in `CODE_DIR`, then use `mcp__augment-context-engine__codebase-retrieval` to understand module responsibilities and inter-module relationships. Use Read for files that need detailed inspection.

Produce TWO outputs:

**Output A: Code Structure Index** — Save to `WORKSPACE/foundation/code_structure_index.md`.
This is a structured file map that Codex and Gemini will use. Format:
```
## Code Structure Index
### [module_path/]
- `filename.py` — one-line description | key classes/functions: ClassA, func_b, func_c
```
List EVERY source file (excluding static assets, icons, example code). For each file include:
- Full relative path from CODE_DIR
- One-line responsibility description
- Key classes and functions by name
- Recommended reading order (number each file 1, 2, 3... by dependency/importance)

**Output B: Claude Understanding Document** — Save to `WORKSPACE/foundation/claude_code_understanding.md`.
Comprehensive understanding document covering:
- System architecture overview
- Core algorithm flow (pseudo-code level)
- Data flow paths
- Key design decisions and rationale
Focus on module-level structure and responsibilities.

**Step 2 — Codex and Gemini analyze in parallel (MUST run after Step 1 completes):**
Verify `WORKSPACE/foundation/code_structure_index.md` exists before proceeding. The script reads this file and embeds it into the prompts for Codex and Gemini, so they can read files directly without exploring.
Run in background, no timeout:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py init-external --code-dir "CODE_DIR" --cd "WORKSPACE"
```
This calls Codex (algorithm-level) and Gemini (architecture-level) in parallel.
Both agents' workspace is set to WORKSPACE, and the prompt directs them to analyze code in CODE_DIR (which is WORKSPACE/code).
Wait for it to complete, then verify success from the JSON output.

**Step 3 — You synthesize all three analyses:**
Read these three files:
- `WORKSPACE/foundation/claude_code_understanding.md` (your analysis)
- `WORKSPACE/foundation/codex_code_understanding.md` (Codex's analysis)
- `WORKSPACE/foundation/gemini_code_understanding.md` (Gemini's analysis)

Synthesize them into a single, comprehensive flow document. Resolve contradictions by favoring the most specific/accurate description. Save to `WORKSPACE/foundation/flow_document.md`.

**After**: Tell user to review `flow_document.md` and confirm accuracy before proceeding.

---

### Phase 2: 写作准备 (Writing Preparation)

**Trigger**: User says "写作规范"、"设置写作规范"、"写作准备"、"大纲"、"参考资料"、"outline"、"references"、"Stage 2"

**Before running**: Ask user for:
1. `WORKSPACE`: 论文工作空间路径

**Convention**: `MATERIALS_DIR` = `WORKSPACE/materials`. The user places their preparation files in this directory before running. Expected files (all optional):
- `MATERIALS_DIR/write_paper_skill.md` — 写作规范
- `MATERIALS_DIR/outline.md` — 论文大纲
- `MATERIALS_DIR/references.md` — 参考资料（任何对写作有用的内容：参考文献、相关段落、说明、笔记等）

If `MATERIALS_DIR` does not exist, tell the user to create it and place their files there.

**Action**:
1. Ensure `WORKSPACE/foundation` directory exists (create via Bash `mkdir` if needed).
2. Check each file in `MATERIALS_DIR` and **use Bash `copy` command** (NOT Read/Write tools) to copy them — this is much faster for large files:
   - If `write_paper_skill.md` exists → `copy "MATERIALS_DIR\write_paper_skill.md" "WORKSPACE\foundation\write_paper_skill.md"`
   - If `outline.md` exists → `copy "MATERIALS_DIR\outline.md" "WORKSPACE\foundation\outline.md"`
   - If `references.md` exists → `copy "MATERIALS_DIR\references.md" "WORKSPACE\foundation\references.md"`
3. For each file found, confirm to the user. For each file not found, inform the user (but do not block).
4. If `write_paper_skill.md` is not provided, inform the user the default `TRIVIUM_HOME/templates/structure_guide.md` will be used automatically during writing.

---

### Phase 3: 写段落 (Write Paragraph)

**Trigger**: User says "写段落"、"写第X章"、"Stage 3"、"write"

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
- `WORKSPACE/foundation/outline.md` → paper outline (may not exist)
- `WORKSPACE/foundation/references.md` → reference materials (may not exist)
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

##### Step 4: Unified Review + Validation (3 agents, same template, explicit discussion)

**4a. You review using the unified template:**
Read `TRIVIUM_HOME/templates/review_unified.md` for review instructions.
Review `CURRENT_DRAFT_FILE` following those instructions across ALL three dimensions (code consistency, research soundness, skill compliance). Use the flow_document and writing standard as references.
Save your review as JSON to `BATCH_DIR/review_round_{ROUND}/claude_review.json`. Use the unified output format:
```json
{"issues": [{"dimension": "...", "type": "...", "sentence": "...", "severity": "...", "reason": "...", "suggestion": "..."}]}
```

**4b. Codex and Gemini review in parallel (MUST run after 4a so your review file exists):**
Run in background:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py review-external --cd "WORKSPACE" --batch-dir "BATCH_DIR" --round ROUND --draft-file "CURRENT_DRAFT_FILE"
```
Wait for completion. The script saves `codex_review.json` and `gemini_review.json` to `BATCH_DIR/review_round_{ROUND}/`.

**4c. You validate the combined issue list:**
Read all three review files:
- `BATCH_DIR/review_round_{ROUND}/claude_review.json`
- `BATCH_DIR/review_round_{ROUND}/codex_review.json`
- `BATCH_DIR/review_round_{ROUND}/gemini_review.json`

Also read `BATCH_DIR/review_round_{ROUND}/all_issues.md` (generated by the validate script in 4d, but if you are running 4c before 4d, manually combine all issues into a numbered list yourself).

For EACH issue across all three reviews, decide accept or reject — is this a genuine problem that needs fixing, or a false positive / stylistic nitpick? Be rigorous: only accept factual errors, logical contradictions, terminology inconsistencies, or clear standard violations.
Save your validation as JSON to `BATCH_DIR/review_round_{ROUND}/claude_validation.json`:
```json
{"validations": [{"issue_id": 1, "vote": "accept|reject", "reason": "..."}]}
```

**4d. Codex and Gemini validate in parallel (MUST run after 4c so your validation file exists):**
Run in background:
```bash
python TRIVIUM_HOME/scripts/paper_workflow.py validate-external --cd "WORKSPACE" --batch-dir "BATCH_DIR" --round ROUND --draft-file "CURRENT_DRAFT_FILE"
```
The script collects all three reviews into a numbered issue list (`all_issues.md`), sends it to Codex and Gemini for accept/reject voting, then loads your `claude_validation.json` and tallies votes. An issue is kept only if **>= 2 out of 3 agents** vote accept. Results are saved to `BATCH_DIR/review_round_{ROUND}/validated_issues.json`.

**4e. Read the validated result:**
Read `BATCH_DIR/review_round_{ROUND}/validated_issues.json`. The `issues` array contains only issues that passed validation. The `vote_details` array shows per-issue accept counts and voter reasons.

##### Step 5: Dual-Track Revision

Read `BATCH_DIR/review_round_{ROUND}/validated_issues.json`.

Count the issues in the `issues` array. If zero issues (validation filtered everything out), skip revision and go directly to Step 6.

If there are issues:

**Track A — Content Fix:**
Read `TRIVIUM_HOME/templates/revision_track_a.md` for instructions.
Use `CURRENT_DRAFT_FILE` as the draft under review. Use `BATCH_DIR/review_round_{ROUND}/validated_issues.json` as the review issues input (these are issues that passed validation by all three agents).
Process every issue: ACCEPT (apply fix), REJECT (explain why original is correct), or PARTIALLY ADOPT (apply better fix). Issues with dimension `code_consistency` are MANDATORY to fix.
Save revision decisions to `BATCH_DIR/revision_round_{ROUND}/revision_log.md`.
Save revised paragraph to `BATCH_DIR/revision_round_{ROUND}/revised_A.md`.

**Track B1 — Academic Polish (input: Track A output):**
Read `TRIVIUM_HOME/templates/revision_track_b_polish.md` for instructions.
Apply these instructions to `BATCH_DIR/revision_round_{ROUND}/revised_A.md`.
Apply Gopen & Swan 7 principles, fix grammar, improve sentence flow.
Save to `BATCH_DIR/revision_round_{ROUND}/revised_B1_polish.md`.

**Track B2 — De-AI (input: Track B1 output):**
Read `TRIVIUM_HOME/templates/revision_track_b_deai.md` for instructions.
Apply these instructions to `BATCH_DIR/revision_round_{ROUND}/revised_B1_polish.md` (NOT revised_A.md).
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

### 恢复/查看状态 (Resume / Check Status)

**Trigger**: User says "查看状态"、"当前进度"、"resume"、"恢复"

**Before running**: Ask user for:
1. `WORKSPACE`: 论文工作空间路径

**Action**: Read `WORKSPACE/paper.md` and report how many paragraphs have been written. List the directories under `WORKSPACE/drafts/` to show which paragraphs have been worked on. For each, check if a `verdict_round_*.json` with consensus exists.

---

## Important Rules

1. **Always run Python scripts in background** with no timeout — external agent calls can be slow.
2. **Proxy**: Gemini calls need proxy. This is handled automatically by `config.json`. If user has proxy issues, tell them to edit `TRIVIUM_HOME/config.json`.
3. **Never skip phases**: If user asks to write paragraphs but `flow_document.md` doesn't exist, remind them to run Phase 1 "理解代码" first.
4. **User intervention points**:
   - After Phase 1 理解代码: user must confirm `flow_document.md`
   - After Phase 2 写作准备: user must confirm materials are loaded
   - After Phase 3 写段落: if consensus fails, user decides
5. **Language**: Interact with user in Chinese. Your own drafting/review/revision work should produce English academic text (unless the paper is in Chinese).
6. **Workspace reuse**: If user has been working in a specific workspace during this session, remember it and don't ask again.
7. **Templates are instructions, not prompts**: When told to "read template X for instructions", you should read the template file, understand its rules and constraints, and follow them directly in your work. Do NOT pass the template to any subprocess.

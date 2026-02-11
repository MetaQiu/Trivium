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

The above resolved path is `TRIVIUM_HOME`. All script references below use it:
- Orchestrator: `TRIVIUM_HOME/scripts/paper_workflow.py`
- Config: `TRIVIUM_HOME/config.json`
- Templates: `TRIVIUM_HOME/templates/`

If the path resolved to `NOT_FOUND`, tell the user to check their installation (see README.md).

## Phases

This skill has distinct phases. Execute ONLY the phase the user requests. Never skip ahead.

---

### Phase: 理解代码 (Code Understanding)

**Trigger**: User says "理解代码"、"分析代码"、"Stage 0.1"、"init", or passes argument "init"

**Before running**: Ask user for:
1. `CODE_DIR`: 代码目录路径 (the source code to analyze)
2. `WORKSPACE`: 论文工作空间路径 (where outputs will be saved)

**Action**: Run in background, no timeout:

```bash
python TRIVIUM_HOME/scripts/paper_workflow.py --mode init --code-dir "CODE_DIR" --cd "WORKSPACE"
```

Replace `TRIVIUM_HOME`, `CODE_DIR`, `WORKSPACE` with the resolved/collected values.

**After running**: Tell user to review `WORKSPACE/foundation/flow_document.md` and confirm accuracy.

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

**Action**: Run in background, no timeout:

```bash
python TRIVIUM_HOME/scripts/paper_workflow.py --mode write --chapter CHAPTER --paragraph PARAGRAPH --cd "WORKSPACE" --PROMPT "PROMPT"
```

Replace all placeholders with the resolved/collected values.

**After running**: Report consensus result. If consensus failed after max rounds, show remaining issues and ask user to decide.

---

### Phase: 恢复/查看状态 (Resume / Check Status)

**Trigger**: User says "查看状态"、"当前进度"、"resume"、"恢复"

**Before running**: Ask user for:
1. `WORKSPACE`: 论文工作空间路径

**Action**:

```bash
python TRIVIUM_HOME/scripts/paper_workflow.py --mode resume --cd "WORKSPACE"
```

If there is an interrupted task, it will automatically resume from the last checkpoint.
If there is no interrupted task, it will display the current state overview.

---

## Important Rules

1. **Always run scripts in background** with no timeout — agent calls (Claude/Codex/Gemini) can be very slow.
2. **Proxy**: Gemini calls need proxy. This is handled automatically by `config.json`. If user has proxy issues, tell them to edit `TRIVIUM_HOME/config.json`.
3. **Never skip phases**: If user asks to write paragraphs but `flow_document.md` doesn't exist, remind them to run "理解代码" first.
4. **User intervention points**:
   - After Phase 理解代码: user must confirm `flow_document.md`
   - After Phase 写作规范: user must confirm `write_paper_skill.md`
   - After Phase 写段落: if consensus fails, user decides
5. **Language**: Interact with user in Chinese. Prompts to Codex/Gemini are in English.
6. **Workspace reuse**: If user has been working in a specific workspace during this session, remember it and don't ask again.

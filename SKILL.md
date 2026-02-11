---
name: trivium
description: >
  Multi-agent collaborative paper writing. Orchestrates Claude Code, Codex CLI, and Gemini CLI
  to independently draft, cross-review, argue, and reach consensus on academic paper paragraphs.
  Activate when user mentions: 论文写作、写论文、Trivium、理解代码、写作规范、写段落、论文审稿.
---

## Phases

This skill has distinct phases. Execute ONLY the phase the user requests. Never skip ahead.

---

### Phase: 理解代码 (Code Understanding)

**Trigger**: User says "理解代码"、"分析代码"、"Stage 0.1"、"init"

**Action**: Run in background, no timeout:

```bash
python {SKILL_DIR}/scripts/paper_workflow.py --mode init --code-dir "{USER_CODE_DIR}" --cd "{USER_WORKSPACE}"
```

**Before running**: Ask user for:
1. `code-dir`: 代码目录路径
2. `cd`: 论文工作空间路径（存放产出物的目录）

**After running**: Tell user to review `{workspace}/foundation/flow_document.md` and confirm accuracy.

---

### Phase: 写作规范 (Writing SKILL)

**Trigger**: User says "写作规范"、"设置写作规范"、"Stage 0.2"

**Action**: User provides their own writing SKILL file. Copy it to `{USER_WORKSPACE}/foundation/write_paper_skill.md`.

**Before running**: Ask user for:
1. 写作规范文件的路径
2. `cd`: 论文工作空间路径

**Note**: This phase does NOT call any script. Just copy the user's file into the correct location.

---

### Phase: 写段落 (Write Paragraph)

**Trigger**: User says "写段落"、"写第X章"、"Stage 1"、"write"

**Action**: Run in background, no timeout:

```bash
python {SKILL_DIR}/scripts/paper_workflow.py --mode write --chapter {N} --paragraph {N} --cd "{USER_WORKSPACE}" --PROMPT "{USER_INSTRUCTION}"
```

**Before running**: Ask user for:
1. `chapter`: 章节号
2. `paragraph`: 段落号
3. `PROMPT`: 本段写作要求（论点、要覆盖的内容）
4. `cd`: 论文工作空间路径

**After running**: Report consensus result. If consensus failed after max rounds, show remaining issues and ask user to decide.

---

### Phase: 查看状态 (Check Status)

**Trigger**: User says "查看状态"、"当前进度"、"resume"

**Action**:

```bash
python {SKILL_DIR}/scripts/paper_workflow.py --mode resume --cd "{USER_WORKSPACE}"
```

---

## Variable Resolution

- `{SKILL_DIR}`: The directory where this SKILL.md is located (resolve at runtime)
- `{USER_WORKSPACE}`: User's paper workspace directory (ask user if unknown)
- `{USER_CODE_DIR}`: User's source code directory (ask user if unknown)

## Important Rules

1. **Always run scripts in background** with no timeout — agent calls can be slow.
2. **Proxy**: Gemini calls need proxy. This is handled automatically by `config.json`.
3. **Never skip phases**: If user asks to write paragraphs but `flow_document.md` doesn't exist, remind them to run "理解代码" first.
4. **User intervention points**:
   - After Phase 理解代码: user must confirm `flow_document.md`
   - After Phase 写作规范: user must confirm `write_paper_skill.md`
   - After Phase 写段落: if consensus fails, user decides
5. **Language**: Interact with user in Chinese. Prompts to Codex/Gemini in English.

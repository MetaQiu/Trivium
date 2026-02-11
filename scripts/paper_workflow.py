"""
Trivium - External Agent Coordinator

Handles Codex CLI and Gemini CLI calls for the Trivium collaborative writing workflow.
Claude's work is done directly by the current Claude Code session (orchestrated by SKILL.md).
This script only manages the external agent calls that require subprocess execution.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(project_root: Path) -> dict:
    config_path = project_root / "config.json"
    if not config_path.exists():
        print(json.dumps({"success": False, "error": f"config.json not found at {config_path}"}))
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Template Formatting
# ---------------------------------------------------------------------------

def safe_format(template: str, **kwargs) -> str:
    """Replace only known {key} placeholders, leaving other braces (e.g. JSON) intact."""
    def replacer(match):
        key = match.group(1)
        if key in kwargs:
            return str(kwargs[key])
        return match.group(0)
    return re.sub(r'\{(\w+)\}', replacer, template)


# ---------------------------------------------------------------------------
# Agent Callers (Codex & Gemini only)
# ---------------------------------------------------------------------------

def _get_agent_timeout(config: dict) -> int:
    return config.get("workflow", {}).get("agent_timeout", 600)


def check_agent_result(result: dict, agent_name: str) -> str:
    """Extract agent_messages from bridge result, warn on failure."""
    if not result.get("success", False):
        error = result.get("error", "unknown error")
        print(f"  [warn] {agent_name} call failed: {error[:300]}", file=sys.stderr)
        return ""
    return result.get("agent_messages", "")


def call_codex(prompt: str, workspace: str, config: dict, project_root: Path,
               session_id: str = "") -> dict:
    """Call Codex CLI via bridge script, return parsed JSON response."""
    bridge = project_root / config["bridges"]["codex"]
    cmd = [
        sys.executable, str(bridge),
        "--cd", workspace,
        "--PROMPT", prompt,
    ]
    if session_id:
        cmd.extend(["--SESSION_ID", session_id])

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=_get_agent_timeout(config),
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"JSON parse failed: {result.stdout[:500]}"}


def call_gemini(prompt: str, workspace: str, config: dict, project_root: Path,
                session_id: str = "") -> dict:
    """Call Gemini CLI via bridge script, return parsed JSON response."""
    bridge = project_root / config["bridges"]["gemini"]
    cmd = [
        sys.executable, str(bridge),
        "--cd", workspace,
        "--PROMPT", prompt,
    ]
    if session_id:
        cmd.extend(["--SESSION_ID", session_id])

    env = os.environ.copy()
    proxy_cfg = config.get("proxy", {})
    if proxy_cfg.get("enabled"):
        env["HTTP_PROXY"] = proxy_cfg.get("http", "")
        env["HTTPS_PROXY"] = proxy_cfg.get("https", "")

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=_get_agent_timeout(config),
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"JSON parse failed: {result.stdout[:500]}"}


def call_codex_and_gemini_parallel(
    codex_prompt: str, gemini_prompt: str,
    workspace: str, config: dict, project_root: Path,
) -> tuple[dict, dict]:
    """Call Codex and Gemini in parallel, return both responses."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        codex_future = pool.submit(call_codex, codex_prompt, workspace, config, project_root)
        gemini_future = pool.submit(call_gemini, gemini_prompt, workspace, config, project_root)
        codex_result = codex_future.result()
        gemini_result = gemini_future.result()
    return codex_result, gemini_result


def prompt_via_file(
    prompt: str, save_path: Path,
) -> str:
    """Write full prompt to a file and return a short meta-prompt referencing it.

    This avoids Windows 32KB command line length limits. The external agent
    reads the file using its own filesystem tools.
    """
    write_file(save_path, prompt)
    abs_path = save_path.resolve()
    return (
        f"Read the file at {abs_path} for your complete task instructions. "
        "Follow them exactly and produce only the requested output."
    )


# ---------------------------------------------------------------------------
# File Helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_template(project_root: Path, name: str) -> str:
    tpl_path = project_root / "templates" / name
    if not tpl_path.exists():
        return ""
    return tpl_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Context Builder
# ---------------------------------------------------------------------------

def build_context_bundle(workspace: Path, chapter: int, paragraph: int,
                         instruction: str, project_root: Path) -> dict:
    foundation = workspace / "foundation"
    return {
        "flow_document": read_file(foundation / "flow_document.md"),
        "write_paper_skill": read_file(foundation / "write_paper_skill.md") or load_template(project_root, "structure_guide.md"),
        "previous_paragraphs": read_file(workspace / "paper.md"),
        "current_instruction": instruction,
        "chapter": chapter,
        "paragraph": paragraph,
    }


# ---------------------------------------------------------------------------
# JSON Response Parsers
# ---------------------------------------------------------------------------

def parse_review(raw: str, fallback_dim: str) -> dict:
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        return {"dimension": fallback_dim, "issues": [], "parse_error": raw[:500]}


def parse_verdict(raw: str) -> dict:
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return {"verdict": "reject", "remaining_issues": [
            {"severity": "critical", "description": f"Agent returned unparseable response: {raw[:200]}"}
        ], "parse_error": raw[:500]}


# ---------------------------------------------------------------------------
# Subcommand: init-external
# ---------------------------------------------------------------------------

def cmd_init_external(args, config: dict, project_root: Path) -> None:
    """Codex + Gemini analyze codebase in parallel. Claude analyzes separately."""
    workspace = args.cd.resolve()
    code_dir = args.code_dir
    foundation = ensure_dir(workspace / "foundation")

    prompt_base = (
        f"Read and analyze the codebase at {code_dir}. "
        "Produce a comprehensive understanding document covering: "
        "1) System architecture overview, "
        "2) Core algorithm flow (pseudo-code level), "
        "3) Data flow paths, "
        "4) Key design decisions and rationale. "
        "Output in Markdown. Be precise and factual, only describe what the code actually does."
    )

    print(f"  [Codex + Gemini] Analyzing codebase in parallel...", file=sys.stderr)

    prompts_dir = ensure_dir(foundation / "_prompts")
    codex_full = f"{prompt_base}\nFocus on: algorithm and logic-level details."
    gemini_full = f"{prompt_base}\nFocus on: architecture and data-flow level details."

    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=prompt_via_file(codex_full, prompts_dir / "init_codex.md"),
        gemini_prompt=prompt_via_file(gemini_full, prompts_dir / "init_gemini.md"),
        workspace=code_dir, config=config, project_root=project_root,
    )

    codex_text = check_agent_result(codex_result, "Codex")
    gemini_text = check_agent_result(gemini_result, "Gemini")

    codex_path = foundation / "codex_code_understanding.md"
    gemini_path = foundation / "gemini_code_understanding.md"
    write_file(codex_path, codex_text)
    write_file(gemini_path, gemini_text)

    result = {
        "success": True,
        "codex_file": str(codex_path),
        "gemini_file": str(gemini_path),
        "codex_empty": len(codex_text.strip()) == 0,
        "gemini_empty": len(gemini_text.strip()) == 0,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Subcommand: draft-external
# ---------------------------------------------------------------------------

def cmd_draft_external(args, config: dict, project_root: Path) -> None:
    """Codex + Gemini draft paragraph in parallel. Claude drafts separately."""
    workspace = args.cd.resolve()
    chapter = args.chapter
    paragraph = args.paragraph
    instruction = args.instruction

    batch_dir = ensure_dir(workspace / "drafts" / f"ch{chapter}_p{paragraph}")
    context = build_context_bundle(workspace, chapter, paragraph, instruction, project_root)

    tpl = load_template(project_root, "draft_prompt.md")
    if not tpl:
        print(json.dumps({"success": False, "error": "draft_prompt.md template not found"}))
        return

    prompt = safe_format(tpl, **context)

    prompts_dir = ensure_dir(batch_dir / "_prompts")
    print(f"  [Codex + Gemini] Drafting in parallel...", file=sys.stderr)
    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=prompt_via_file(prompt, prompts_dir / "draft.md"),
        gemini_prompt=prompt_via_file(prompt, prompts_dir / "draft.md"),
        workspace=str(workspace), config=config, project_root=project_root,
    )

    codex_draft = check_agent_result(codex_result, "Codex")
    gemini_draft = check_agent_result(gemini_result, "Gemini")

    codex_path = batch_dir / "codex_draft.md"
    gemini_path = batch_dir / "gemini_draft.md"
    write_file(codex_path, codex_draft)
    write_file(gemini_path, gemini_draft)

    result = {
        "success": True,
        "batch_dir": str(batch_dir),
        "codex_file": str(codex_path),
        "gemini_file": str(gemini_path),
        "codex_empty": len(codex_draft.strip()) == 0,
        "gemini_empty": len(gemini_draft.strip()) == 0,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Subcommand: review-external
# ---------------------------------------------------------------------------

def cmd_review_external(args, config: dict, project_root: Path) -> None:
    """Codex (code consistency) + Gemini (skill compliance) review in parallel."""
    workspace = args.cd.resolve()
    batch_dir = Path(args.batch_dir).resolve()
    round_num = args.round
    draft_file = Path(args.draft_file).resolve()

    review_dir = ensure_dir(batch_dir / f"review_round_{round_num}")

    draft_text = read_file(draft_file)
    if not draft_text.strip():
        print(json.dumps({"success": False, "error": f"Draft file is empty: {draft_file}"}))
        return

    foundation = workspace / "foundation"
    flow_document = read_file(foundation / "flow_document.md")
    write_paper_skill = read_file(foundation / "write_paper_skill.md") or load_template(project_root, "structure_guide.md")

    # Build review prompts
    codex_prompt = safe_format(
        load_template(project_root, "review_code_consistency.md"),
        merged_draft=draft_text,
        flow_document=flow_document,
    )
    gemini_prompt = safe_format(
        load_template(project_root, "review_skill_compliance.md"),
        merged_draft=draft_text,
        write_paper_skill=write_paper_skill,
    )

    prompts_dir = ensure_dir(review_dir / "_prompts")
    print(f"  [Codex + Gemini] Reviewing in parallel (round {round_num})...", file=sys.stderr)
    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=prompt_via_file(codex_prompt, prompts_dir / "review_codex.md"),
        gemini_prompt=prompt_via_file(gemini_prompt, prompts_dir / "review_gemini.md"),
        workspace=str(workspace), config=config, project_root=project_root,
    )

    code_review = parse_review(check_agent_result(codex_result, "Codex"), "code_consistency")
    skill_review = parse_review(check_agent_result(gemini_result, "Gemini"), "skill_compliance")

    code_path = review_dir / "code_consistency.json"
    skill_path = review_dir / "skill_compliance.json"
    write_file(code_path, json.dumps(code_review, indent=2, ensure_ascii=False))
    write_file(skill_path, json.dumps(skill_review, indent=2, ensure_ascii=False))

    result = {
        "success": True,
        "review_dir": str(review_dir),
        "code_consistency": code_review,
        "skill_compliance": skill_review,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Subcommand: vote-external
# ---------------------------------------------------------------------------

def cmd_vote_external(args, config: dict, project_root: Path) -> None:
    """Codex + Gemini vote on final draft in parallel."""
    workspace = args.cd.resolve()
    batch_dir = Path(args.batch_dir).resolve()
    round_num = args.round
    draft_file = Path(args.draft_file).resolve()

    final_draft = read_file(draft_file)
    if not final_draft.strip():
        print(json.dumps({"success": False, "error": f"Draft file is empty: {draft_file}"}))
        return

    # Read revision log (may not exist if step 5 was skipped)
    revision_dir = batch_dir / f"revision_round_{round_num}"
    revision_log = read_file(revision_dir / "revision_log.md")
    flow_document = read_file(workspace / "foundation" / "flow_document.md")

    vote_prompt_text = safe_format(
        load_template(project_root, "vote_prompt.md"),
        final_draft=final_draft,
        revision_log=revision_log,
        flow_document=flow_document,
    )

    prompts_dir = ensure_dir(batch_dir / "_prompts")
    prompt_file = prompts_dir / f"vote_round_{round_num}.md"
    print(f"  [Codex + Gemini] Voting (round {round_num})...", file=sys.stderr)
    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=prompt_via_file(vote_prompt_text, prompt_file),
        gemini_prompt=prompt_via_file(vote_prompt_text, prompt_file),
        workspace=str(workspace), config=config, project_root=project_root,
    )

    codex_verdict = parse_verdict(check_agent_result(codex_result, "Codex"))
    gemini_verdict = parse_verdict(check_agent_result(gemini_result, "Gemini"))

    verdicts = {"codex": codex_verdict, "gemini": gemini_verdict}
    write_file(batch_dir / f"verdict_round_{round_num}.json",
               json.dumps(verdicts, indent=2, ensure_ascii=False))

    consensus_mode = config.get("workflow", {}).get("consensus_mode", "strict")
    codex_approved = codex_verdict.get("verdict") == "approve"
    gemini_approved = gemini_verdict.get("verdict") == "approve"

    if consensus_mode == "strict":
        passed = codex_approved and gemini_approved
    else:
        passed = codex_approved or gemini_approved

    remaining = []
    if not codex_approved:
        remaining.extend(codex_verdict.get("remaining_issues", []))
    if not gemini_approved:
        remaining.extend(gemini_verdict.get("remaining_issues", []))

    result = {
        "success": True,
        "consensus": passed,
        "codex_verdict": "approve" if codex_approved else "reject",
        "gemini_verdict": "approve" if gemini_approved else "reject",
        "remaining_issues": remaining,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Trivium - External Agent Coordinator (Codex & Gemini)"
    )
    subparsers = parser.add_subparsers(dest="step", required=True,
                                        help="Workflow step to execute")

    # init-external
    p_init = subparsers.add_parser("init-external",
        help="Codex + Gemini analyze codebase in parallel")
    p_init.add_argument("--code-dir", required=True, type=str,
        help="Source code directory to analyze")
    p_init.add_argument("--cd", required=True, type=Path,
        help="Paper workspace directory")

    # draft-external
    p_draft = subparsers.add_parser("draft-external",
        help="Codex + Gemini draft paragraph in parallel")
    p_draft.add_argument("--cd", required=True, type=Path,
        help="Paper workspace directory")
    p_draft.add_argument("--chapter", required=True, type=int)
    p_draft.add_argument("--paragraph", required=True, type=int)
    p_draft.add_argument("--instruction", required=True, type=str,
        help="Writing instruction for this paragraph")

    # review-external
    p_review = subparsers.add_parser("review-external",
        help="Codex (code consistency) + Gemini (skill compliance) review in parallel")
    p_review.add_argument("--cd", required=True, type=Path,
        help="Paper workspace directory")
    p_review.add_argument("--batch-dir", required=True, type=str,
        help="Batch directory for this paragraph")
    p_review.add_argument("--round", required=True, type=int,
        help="Debate round number")
    p_review.add_argument("--draft-file", required=True, type=str,
        help="Path to the draft file to review")

    # vote-external
    p_vote = subparsers.add_parser("vote-external",
        help="Codex + Gemini vote on final draft in parallel")
    p_vote.add_argument("--cd", required=True, type=Path,
        help="Paper workspace directory")
    p_vote.add_argument("--batch-dir", required=True, type=str,
        help="Batch directory for this paragraph")
    p_vote.add_argument("--round", required=True, type=int,
        help="Debate round number")
    p_vote.add_argument("--draft-file", required=True, type=str,
        help="Path to the final draft file to vote on")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    config = load_config(project_root)

    if args.step == "init-external":
        cmd_init_external(args, config, project_root)
    elif args.step == "draft-external":
        cmd_draft_external(args, config, project_root)
    elif args.step == "review-external":
        cmd_review_external(args, config, project_root)
    elif args.step == "vote-external":
        cmd_vote_external(args, config, project_root)


if __name__ == "__main__":
    main()

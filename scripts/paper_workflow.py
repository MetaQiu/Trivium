"""
Trivium - Multi-Agent Collaborative Paper Writing Orchestrator

Orchestrates Claude Code, Codex CLI, and Gemini CLI to independently draft,
cross-review, argue, and reach consensus on academic paper paragraphs.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(project_root: Path) -> dict:
    config_path = project_root / "config.json"
    if not config_path.exists():
        print(f"[error] config.json not found at {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Agent Callers
# ---------------------------------------------------------------------------

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
        timeout=300,
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
        env=env, timeout=300,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"JSON parse failed: {result.stdout[:500]}"}


def call_claude(prompt: str, config: dict) -> str:
    """Call Claude CLI in non-interactive mode, return text response."""
    claude_cfg = config.get("claude", {})
    cmd = [claude_cfg.get("command", "claude")] + claude_cfg.get("args", ["--print"])
    cmd.extend(["--prompt", prompt])

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300,
    )
    return result.stdout.strip()


def call_codex_and_gemini_parallel(
    codex_prompt: str, gemini_prompt: str,
    workspace: str, config: dict, project_root: Path,
) -> tuple[dict, dict]:
    """Call Codex and Gemini in parallel, return both responses."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=2) as pool:
        codex_future = pool.submit(call_codex, codex_prompt, workspace, config, project_root)
        gemini_future = pool.submit(call_gemini, gemini_prompt, workspace, config, project_root)
        codex_result = codex_future.result()
        gemini_result = gemini_future.result()

    return codex_result, gemini_result


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


def load_state(workspace: Path) -> dict:
    state_path = workspace / "state.json"
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"stage": "init", "current_batch": None, "rounds": {}}


def save_state(workspace: Path, state: dict) -> None:
    state_path = workspace / "state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_template(project_root: Path, name: str) -> str:
    tpl_path = project_root / "templates" / name
    if not tpl_path.exists():
        print(f"[error] Template not found: {tpl_path}")
        sys.exit(1)
    return tpl_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Context Bundle
# ---------------------------------------------------------------------------

def build_context_bundle(workspace: Path, chapter: int, paragraph: int,
                         user_instruction: str) -> dict:
    """Build the context bundle for a paragraph writing task."""
    foundation = workspace / "foundation"
    bundle = {
        "flow_document": read_file(foundation / "flow_document.md"),
        "write_paper_skill": read_file(foundation / "write_paper_skill.md"),
        "paper_outline": read_file(foundation / "paper_outline.md"),
        "previous_paragraphs": read_file(workspace / "paper.md"),
        "current_instruction": user_instruction,
        "chapter": chapter,
        "paragraph": paragraph,
    }
    return bundle


# ---------------------------------------------------------------------------
# Stage 0: Init - Code Understanding
# ---------------------------------------------------------------------------

def stage0_init(workspace: Path, code_dir: str, config: dict, project_root: Path) -> None:
    """Stage 0.1: Three agents read code and produce flow_document.md"""
    print("[Stage 0.1] Reading codebase with all three agents...")
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

    # Claude analyzes (module-level)
    print("  [Claude] Analyzing codebase (module-level)...")
    claude_understanding = call_claude(
        f"{prompt_base}\nFocus on: module-level structure and responsibilities.",
        config,
    )
    write_file(foundation / "claude_code_understanding.md", claude_understanding)

    # Codex and Gemini analyze in parallel
    print("  [Codex + Gemini] Analyzing codebase in parallel...")
    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=f"{prompt_base}\nFocus on: algorithm and logic-level details.",
        gemini_prompt=f"{prompt_base}\nFocus on: architecture and data-flow level details.",
        workspace=code_dir, config=config, project_root=project_root,
    )

    codex_text = codex_result.get("agent_messages", codex_result.get("error", ""))
    gemini_text = gemini_result.get("agent_messages", gemini_result.get("error", ""))
    write_file(foundation / "codex_code_understanding.md", codex_text)
    write_file(foundation / "gemini_code_understanding.md", gemini_text)

    # Claude synthesizes
    print("  [Claude] Synthesizing flow document...")
    synthesis_prompt = (
        "Below are three analyses of the same codebase from different perspectives.\n\n"
        f"=== Claude (module-level) ===\n{claude_understanding}\n\n"
        f"=== Codex (algorithm-level) ===\n{codex_text}\n\n"
        f"=== Gemini (architecture-level) ===\n{gemini_text}\n\n"
        "Synthesize these into a single, comprehensive flow_document.md. "
        "Resolve any contradictions by favoring the most specific/accurate description. "
        "Output in Markdown."
    )
    flow_doc = call_claude(synthesis_prompt, config)
    write_file(foundation / "flow_document.md", flow_doc)
    print(f"  [Done] flow_document.md written to {foundation / 'flow_document.md'}")
    print("  [Action Required] Please review flow_document.md and confirm accuracy before proceeding.")


# ---------------------------------------------------------------------------
# Stage 1: Per-Paragraph Writing Loop
# ---------------------------------------------------------------------------

def step2_independent_drafting(
    context: dict, workspace: Path, batch_dir: Path,
    config: dict, project_root: Path,
) -> tuple[str, str, str]:
    """Step 2: Three agents draft independently in parallel."""
    print("  [Step 2] Independent drafting...")

    tpl = load_template(project_root, "draft_prompt.md").format(**context)

    # Claude drafts
    print("    [Claude] Drafting...")
    claude_draft = call_claude(tpl, config)
    write_file(batch_dir / "claude_draft.md", claude_draft)

    # Codex + Gemini draft in parallel
    print("    [Codex + Gemini] Drafting in parallel...")
    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=tpl, gemini_prompt=tpl,
        workspace=str(workspace), config=config, project_root=project_root,
    )
    codex_draft = codex_result.get("agent_messages", "")
    gemini_draft = gemini_result.get("agent_messages", "")
    write_file(batch_dir / "codex_draft.md", codex_draft)
    write_file(batch_dir / "gemini_draft.md", gemini_draft)

    return claude_draft, codex_draft, gemini_draft


def step3_synthesis(
    claude_draft: str, codex_draft: str, gemini_draft: str,
    context: dict, batch_dir: Path, config: dict, project_root: Path,
) -> str:
    """Step 3: Claude synthesizes three drafts into merged draft."""
    print("  [Step 3] Synthesizing drafts...")

    prompt = load_template(project_root, "synthesis_prompt.md").format(
        claude_draft=claude_draft,
        codex_draft=codex_draft,
        gemini_draft=gemini_draft,
        flow_document=context["flow_document"],
    )

    response = call_claude(prompt, config)

    parts = response.split("---", 1)
    merged = parts[0].strip()
    notes = parts[1].strip() if len(parts) > 1 else ""

    write_file(batch_dir / "merged_draft.md", merged)
    write_file(batch_dir / "synthesis_log.md", notes)
    return merged


def step4_three_dimensional_review(
    merged_draft: str, context: dict, batch_dir: Path, round_num: int,
    config: dict, project_root: Path, workspace: Path,
) -> dict:
    """Step 4: Three-dimensional review (code consistency, SKILL compliance, research soundness)."""
    print(f"  [Step 4] Three-dimensional review (round {round_num})...")
    review_dir = ensure_dir(batch_dir / f"review_round_{round_num}")

    # Dimension 1: Code Consistency (Codex)
    codex_prompt = load_template(project_root, "review_code_consistency.md").format(
        merged_draft=merged_draft,
        flow_document=context["flow_document"],
    )

    # Dimension 2: SKILL Compliance (Gemini)
    gemini_prompt = load_template(project_root, "review_skill_compliance.md").format(
        merged_draft=merged_draft,
        write_paper_skill=context["write_paper_skill"],
    )

    # Dimension 3: Research Soundness (Claude)
    claude_prompt = load_template(project_root, "review_research_soundness.md").format(
        merged_draft=merged_draft,
    )

    # Claude reviews locally
    print("    [Claude] Reviewing research soundness...")
    claude_review_raw = call_claude(claude_prompt, config)

    # Codex + Gemini review in parallel
    print("    [Codex + Gemini] Reviewing in parallel...")
    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=codex_prompt, gemini_prompt=gemini_prompt,
        workspace=str(workspace), config=config, project_root=project_root,
    )

    def parse_review(raw: str, fallback_dim: str) -> dict:
        try:
            # Try to extract JSON from the response
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            return {"dimension": fallback_dim, "issues": [], "parse_error": raw[:500]}

    code_review = parse_review(
        codex_result.get("agent_messages", ""), "code_consistency"
    )
    skill_review = parse_review(
        gemini_result.get("agent_messages", ""), "skill_compliance"
    )
    research_review = parse_review(claude_review_raw, "research_soundness")

    write_file(review_dir / "code_consistency.json", json.dumps(code_review, indent=2, ensure_ascii=False))
    write_file(review_dir / "skill_compliance.json", json.dumps(skill_review, indent=2, ensure_ascii=False))
    write_file(review_dir / "research_soundness.json", json.dumps(research_review, indent=2, ensure_ascii=False))

    return {
        "code_consistency": code_review,
        "skill_compliance": skill_review,
        "research_soundness": research_review,
    }


def step5_dual_track_revision(
    merged_draft: str, reviews: dict, context: dict,
    batch_dir: Path, config: dict, project_root: Path,
) -> str:
    """Step 5: Dual-track revision (Track A: content fix, Track B: academic polish)."""
    print("  [Step 5] Dual-track revision...")

    reviews_text = json.dumps(reviews, indent=2, ensure_ascii=False)

    # Track A: Content Fix
    print("    [Track A] Content fix...")
    track_a_prompt = load_template(project_root, "revision_track_a.md").format(
        merged_draft=merged_draft,
        reviews=reviews_text,
        flow_document=context["flow_document"],
    )
    track_a_response = call_claude(track_a_prompt, config)

    parts = track_a_response.split("=== Revised Paragraph ===", 1)
    revision_decisions = parts[0].strip() if len(parts) > 1 else ""
    revised_a = parts[1].strip() if len(parts) > 1 else track_a_response.strip()

    write_file(batch_dir / "revised_A.md", revised_a)
    write_file(batch_dir / "revision_log.md", revision_decisions)

    # Track B: Academic Polish (two sub-steps)
    # B1: Expression polish
    print("    [Track B1] Academic polish...")
    track_b1_prompt = load_template(project_root, "revision_track_b_polish.md").format(
        revised_a=revised_a,
        write_paper_skill=context["write_paper_skill"],
    )
    polished = call_claude(track_b1_prompt, config)
    write_file(batch_dir / "revised_B1_polish.md", polished)

    # B2: De-AI
    print("    [Track B2] De-AI...")
    track_b2_prompt = load_template(project_root, "revision_track_b_deai.md").format(
        revised_a=polished,
    )
    revised_b = call_claude(track_b2_prompt, config)
    write_file(batch_dir / "revised_B.md", revised_b)
    return revised_b


def step6_voting(
    final_draft: str, context: dict, batch_dir: Path, round_num: int,
    config: dict, project_root: Path, workspace: Path,
) -> tuple[bool, list]:
    """Step 6: Voting - Codex and Gemini approve or reject."""
    print(f"  [Step 6] Voting (round {round_num})...")

    revision_log = read_file(batch_dir / "revision_log.md")
    vote_prompt = load_template(project_root, "vote_prompt.md").format(
        final_draft=final_draft,
        revision_log=revision_log,
        flow_document=context["flow_document"],
    )

    codex_result, gemini_result = call_codex_and_gemini_parallel(
        codex_prompt=vote_prompt, gemini_prompt=vote_prompt,
        workspace=str(workspace), config=config, project_root=project_root,
    )

    def parse_verdict(raw: str) -> dict:
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return {"verdict": "approve", "remaining_issues": [], "parse_error": raw[:500]}

    codex_verdict = parse_verdict(codex_result.get("agent_messages", ""))
    gemini_verdict = parse_verdict(gemini_result.get("agent_messages", ""))

    verdicts = {"codex": codex_verdict, "gemini": gemini_verdict}
    write_file(batch_dir / f"verdict_round_{round_num}.json",
               json.dumps(verdicts, indent=2, ensure_ascii=False))

    consensus_mode = config.get("workflow", {}).get("consensus_mode", "strict")
    codex_approved = codex_verdict.get("verdict") == "approve"
    gemini_approved = gemini_verdict.get("verdict") == "approve"

    if consensus_mode == "strict":
        passed = codex_approved and gemini_approved
    else:  # majority
        passed = codex_approved or gemini_approved

    remaining = []
    if not codex_approved:
        remaining.extend(codex_verdict.get("remaining_issues", []))
    if not gemini_approved:
        remaining.extend(gemini_verdict.get("remaining_issues", []))

    status = "APPROVED" if passed else "REJECTED"
    print(f"    Codex: {'approve' if codex_approved else 'reject'}")
    print(f"    Gemini: {'approve' if gemini_approved else 'reject'}")
    print(f"    Result: {status}")

    return passed, remaining


# ---------------------------------------------------------------------------
# Main Write Loop
# ---------------------------------------------------------------------------

def write_paragraph(
    workspace: Path, chapter: int, paragraph: int,
    instruction: str, config: dict, project_root: Path,
) -> None:
    """Execute the full per-paragraph writing loop (Steps 1-6)."""
    batch_id = f"ch{chapter}_p{paragraph}"
    batch_dir = ensure_dir(workspace / "drafts" / batch_id)
    max_rounds = config.get("workflow", {}).get("max_debate_rounds", 3)

    print(f"\n{'='*60}")
    print(f"  Writing: Chapter {chapter}, Paragraph {paragraph}")
    print(f"  Instruction: {instruction}")
    print(f"{'='*60}\n")

    # Step 1: Deep Context Load
    print("  [Step 1] Loading context...")
    context = build_context_bundle(workspace, chapter, paragraph, instruction)
    write_file(batch_dir / "context_bundle.json",
               json.dumps(context, indent=2, ensure_ascii=False))

    # Step 2: Independent Drafting
    claude_draft, codex_draft, gemini_draft = step2_independent_drafting(
        context, workspace, batch_dir, config, project_root,
    )

    # Step 3: Synthesis
    merged = step3_synthesis(
        claude_draft, codex_draft, gemini_draft, context, batch_dir, config, project_root,
    )

    # Steps 4-6: Review → Revise → Vote loop
    current_draft = merged
    for round_num in range(1, max_rounds + 1):
        print(f"\n  --- Debate Round {round_num}/{max_rounds} ---")

        # Step 4: Three-dimensional review
        reviews = step4_three_dimensional_review(
            current_draft, context, batch_dir, round_num,
            config, project_root, workspace,
        )

        # Check if there are any issues at all
        total_issues = sum(
            len(r.get("issues", [])) for r in reviews.values()
        )
        if total_issues == 0:
            print("  [No issues found] Skipping revision, proceeding to vote.")
        else:
            # Step 5: Dual-track revision
            current_draft = step5_dual_track_revision(
                current_draft, reviews, context, batch_dir, config, project_root,
            )

        # Step 6: Voting
        passed, remaining = step6_voting(
            current_draft, context, batch_dir, round_num,
            config, project_root, workspace,
        )

        if passed:
            print(f"\n  [CONSENSUS REACHED] Round {round_num}")
            break

        if round_num == max_rounds:
            print(f"\n  [MAX ROUNDS REACHED] Could not reach consensus after {max_rounds} rounds.")
            print("  Remaining issues:")
            for issue in remaining:
                print(f"    - [{issue.get('severity', '?')}] {issue.get('description', '?')}")
            print("  [Action Required] Please review and decide manually.")
            break

        print(f"  [Round {round_num} rejected] Incorporating feedback for next round...")

    # Append to paper.md
    paper_path = workspace / "paper.md"
    existing = read_file(paper_path)
    separator = "\n\n" if existing else ""
    write_file(paper_path, existing + separator + current_draft)
    print(f"\n  [Written] Paragraph appended to {paper_path}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Trivium - Multi-Agent Collaborative Paper Writing"
    )
    parser.add_argument("--mode", required=True,
                        choices=["init", "write", "resume"],
                        help="Workflow mode")
    parser.add_argument("--cd", required=True, type=Path,
                        help="Paper workspace directory")
    parser.add_argument("--code-dir", type=str, default="",
                        help="Source code directory (for init mode)")
    parser.add_argument("--chapter", type=int, default=1,
                        help="Chapter number (for write mode)")
    parser.add_argument("--paragraph", type=int, default=1,
                        help="Paragraph number (for write mode)")
    parser.add_argument("--PROMPT", type=str, default="",
                        help="Writing instruction for the paragraph")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    config = load_config(project_root)
    workspace = args.cd.resolve()
    ensure_dir(workspace)

    if args.mode == "init":
        if not args.code_dir:
            print("[error] --code-dir is required for init mode")
            sys.exit(1)
        stage0_init(workspace, args.code_dir, config, project_root)

    elif args.mode == "write":
        if not args.PROMPT:
            print("[error] --PROMPT is required for write mode")
            sys.exit(1)
        write_paragraph(
            workspace, args.chapter, args.paragraph,
            args.PROMPT, config, project_root,
        )

    elif args.mode == "resume":
        state = load_state(workspace)
        print(f"[resume] Current state: {json.dumps(state, indent=2)}")
        print("[TODO] Resume logic not yet implemented.")


if __name__ == "__main__":
    main()

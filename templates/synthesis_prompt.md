# Synthesis Prompt Template

Below are three independent drafts of the same paragraph from different AI agents.

## Draft A (Claude)

{claude_draft}

## Draft B (Codex)

{codex_draft}

## Draft C (Gemini)

{gemini_draft}

## Factual Constraint

{flow_document}

## Task

1. Compare all three drafts sentence by sentence.
2. For each divergence point, evaluate:
   - Factual accuracy (does it match the code flow document?)
   - Clarity of expression
   - Academic tone and precision
3. Select the best expression from each draft. You may combine parts from different drafts.
4. Ensure the merged result reads as a single coherent paragraph, not a patchwork.
5. Verify the final paragraph against the factual constraint — no technical claim may contradict the code.

## Output Format

Output the merged paragraph first.
Then output a line containing only "---".
Then output synthesis notes explaining your choices (which parts came from which draft and why).

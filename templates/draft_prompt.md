# Draft Prompt Template

Based on the following context, write Chapter {chapter} Paragraph {paragraph}.

## Factual Constraint (GROUND TRUTH - never contradict this)

{flow_document}

## Writing Standard

{write_paper_skill}

## Structure Guide

- One paragraph, one core idea
- Topic sentence first → evidence → analysis → transition to next paragraph
- Every claim must be backed by evidence from the code/experiments or a citation
- Use present tense for methods and conclusions
- Keep within 5-8 sentences unless the content demands more

## Style Rules

- Use simple, precise academic vocabulary. Prefer common words over rare ones.
- Do NOT use contractions (use "does not" instead of "doesn't")
- Do NOT use em dashes (—). Use commas, parentheses, or subordinate clauses instead.
- Do NOT use bullet lists. Write in continuous prose.
- Do NOT use bold or italic for emphasis. Let sentence structure convey importance.
- Avoid copula avoidance: use "is" and "has" naturally, don't force "serves as" or "features"
- No filler phrases: "In order to" → "To", "Due to the fact that" → "Because"

## Sentence Construction (Gopen & Swan Principles)

- Keep subject and verb close — do not separate them with long clauses
- Place the most important information at the END of each sentence (stress position)
- Put context/old information at the BEGINNING of each sentence (topic position)
- Express action in verbs, not nominalizations: "We analyzed" not "We performed an analysis"
- Minimize bare pronouns: "This result shows..." not "This shows..."
- One sentence = one idea. If a sentence carries two ideas, split it.

## Word Precision (Lipton & Steinhardt)

- Replace vague terms: "performance" → "accuracy" or "latency"; "large" → "1B parameters"
- Delete hedging words ("may", "can") unless genuinely uncertain
- Delete intensifiers: "very", "extremely", "highly", "quite", "essentially"
- Use consistent terminology: pick one term per concept and stick with it throughout

## Previous Text (for continuity)

{previous_paragraphs}

## Paragraph Requirement

{current_instruction}

## Output

Output ONLY the paragraph text. No explanations, no headers, no metadata.

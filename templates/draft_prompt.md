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

## Previous Text (for continuity)

{previous_paragraphs}

## Paragraph Requirement

{current_instruction}

## Output

Output ONLY the paragraph text. No explanations, no headers, no metadata.

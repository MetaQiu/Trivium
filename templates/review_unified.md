# Unified Review

## Paragraph Under Review

{merged_draft}

## Reference Materials

### Code Flow Document (GROUND TRUTH)

{flow_document}

### Writing Standard

{write_paper_skill}

## Task

You are a senior academic reviewer. Perform a comprehensive review of the paragraph above across ALL three dimensions below. Only report **actual problems** — if a dimension has no issues, omit it from the output.

### Dimension 1: code_consistency
Check every technical claim against the code flow document.
- Algorithm descriptions — do the steps match the actual implementation?
- Data flow claims — does data actually flow as described?
- Performance/behavior claims — are they supported by actual code behavior?
- Architectural claims — does the system structure match the code?

### Dimension 2: research_soundness
Check logical integrity and factual correctness. Use a high tolerance threshold — only flag issues that block reader comprehension.
- Fatal logic contradictions — are there mutually contradictory statements?
- Terminology consistency — are core concepts renamed without explanation?
- Severe grammar errors — are there Chinglish patterns or structural errors that obscure meaning?

### Dimension 3: skill_compliance
Check against the writing standard.
- Structure: Does it follow topic sentence → evidence → analysis → transition?
- Terminology: Are technical terms used correctly and consistently?
- Citation: Are claims properly attributed where needed?
- Transition: Is there a natural bridge to the next paragraph?
- Tone: No informal language, overclaiming, excessive hedging, or promotional language.

## Output

Return ONLY a JSON object, no other text. If no issues are found in any dimension, return an empty issues array.

```json
{
  "issues": [
    {
      "dimension": "code_consistency | research_soundness | skill_compliance",
      "type": "brief category (e.g. architecture, logic, terminology, structure, tone)",
      "sentence": "the exact sentence from the paragraph that has the issue",
      "severity": "critical | major | minor",
      "reason": "explanation of the problem",
      "suggestion": "how to fix it"
    }
  ]
}
```

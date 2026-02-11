# Review: SKILL Compliance

## Paragraph Under Review

{merged_draft}

## Reference: Writing Standard

{write_paper_skill}

## Task

You are an academic style reviewer. Check this paragraph against the writing standard.

Evaluate the following dimensions:

1. **structure**: Does it follow the expected paragraph pattern (topic sentence → evidence → analysis → transition)?
2. **terminology**: Are technical terms used correctly and consistently? Are common abbreviations kept as-is (LLM, CNN, etc.)?
3. **citation**: Are claims properly attributed? Any claims that need citation but lack one?
4. **transition**: Is there a natural bridge to the next paragraph? Does it connect logically to previous text?
5. **tone**: Is the academic tone appropriate? Check for:
   - Informal language ("a lot of", "pretty good")
   - Overclaiming ("revolutionary", "groundbreaking")
   - Hedging excess ("could potentially possibly")
   - Promotional language ("state-of-the-art" without evidence)

## Output

Return ONLY a JSON object, no other text:

```json
{
  "dimension": "skill_compliance",
  "issues": [
    {
      "type": "structure | terminology | citation | transition | tone",
      "sentence": "the exact sentence with the issue",
      "status": "compliant | non_compliant",
      "reason": "explanation of the violation",
      "suggestion": "how to fix it"
    }
  ]
}
```

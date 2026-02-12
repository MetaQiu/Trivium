# Review: Code Consistency

## Paragraph Under Review

{merged_draft}

## Reference: Code Flow Document (GROUND TRUTH)

{flow_document}

## Task

You are a technical accuracy reviewer. Check every sentence in the paragraph against the code flow document.

For each sentence, check whether the technical description matches what the code actually does. Only report sentences that are **inaccurate** or **unverifiable**. Do NOT include sentences that are accurate — if every sentence is correct, return an empty issues array.

Pay special attention to:
1. Algorithm descriptions — do the steps match the actual implementation?
2. Data flow claims — does data actually flow as described?
3. Performance/behavior claims — are they supported by actual code behavior?
4. Architectural claims — does the system structure match the code?

## Output

Return ONLY a JSON object, no other text. If no issues are found, return `{"dimension": "code_consistency", "issues": []}`.

```json
{
  "dimension": "code_consistency",
  "issues": [
    {
      "sentence": "the exact sentence from the paragraph",
      "status": "inaccurate | unverifiable",
      "reason": "explanation of why",
      "suggestion": "corrected text if inaccurate, empty string if unverifiable"
    }
  ]
}
```

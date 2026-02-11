# Review: Code Consistency

## Paragraph Under Review

{merged_draft}

## Reference: Code Flow Document (GROUND TRUTH)

{flow_document}

## Task

You are a technical accuracy reviewer. Check every sentence in the paragraph against the code flow document.

For each sentence, determine:
- **accurate**: The technical description matches what the code actually does
- **inaccurate**: The description contradicts or misrepresents the code (provide the correct description)
- **unverifiable**: The claim cannot be verified from the code flow document alone

Pay special attention to:
1. Algorithm descriptions — do the steps match the actual implementation?
2. Data flow claims — does data actually flow as described?
3. Performance/behavior claims — are they supported by actual code behavior?
4. Architectural claims — does the system structure match the code?

## Output

Return ONLY a JSON object, no other text:

```json
{
  "dimension": "code_consistency",
  "issues": [
    {
      "sentence": "the exact sentence from the paragraph",
      "status": "accurate | inaccurate | unverifiable",
      "reason": "explanation of why",
      "suggestion": "corrected text if inaccurate, empty string if accurate"
    }
  ]
}
```

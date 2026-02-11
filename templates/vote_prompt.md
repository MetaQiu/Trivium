# Vote Prompt

## Paragraph for Final Approval

{final_draft}

## Revision Log (how previous review issues were handled)

{revision_log}

## Code Flow Document (for fact-checking)

{flow_document}

## Task

You are making a final approval decision on this paragraph.

Check:
1. **Technical accuracy**: Does every technical claim match the code flow document?
2. **Logical coherence**: Is the argument sound and self-consistent?
3. **Academic quality**: Does it read like a publication-ready paragraph?
4. **Review responsiveness**: Were previous review issues adequately addressed?

Decision criteria:
- **approve**: The paragraph is ready for inclusion in the paper. Minor stylistic preferences are NOT grounds for rejection.
- **reject**: There is a factual error, logical flaw, or serious quality issue that MUST be fixed before inclusion. You MUST provide specific remaining issues.

## Output

Return ONLY a JSON object, no other text:

```json
{
  "verdict": "approve | reject",
  "remaining_issues": [
    {
      "severity": "critical | minor",
      "description": "what is wrong",
      "suggestion": "how to fix it"
    }
  ]
}
```

If approving, remaining_issues should be an empty array.

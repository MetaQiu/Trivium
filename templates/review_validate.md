# Issue Validation

You are one of three reviewers. All three reviewers have independently reviewed the same paragraph and produced issues. The combined issue list is below. Your task is to evaluate EACH issue and vote whether it is a genuine problem that requires revision.

## Paragraph Under Review

{merged_draft}

## Reference: Code Flow Document (GROUND TRUTH)

{flow_document}

## Reference: Writing Standard

{write_paper_skill}

## Combined Issue List (from all reviewers)

{all_issues}

## Task

For EACH numbered issue above, decide:
- **accept**: This is a real problem that should be fixed.
- **reject**: This is not a real problem (false positive, stylistic nitpick, or the original text is actually correct).

Be rigorous. Only accept issues that represent genuine errors — factual inaccuracies, logical contradictions, terminology inconsistencies, or clear violations of the writing standard. Reject issues that are merely stylistic preferences or "could be better" suggestions.

## Output

Return ONLY a JSON object, no other text:

```json
{
  "validations": [
    {
      "issue_id": 1,
      "vote": "accept | reject",
      "reason": "brief justification for your vote"
    }
  ]
}
```

You MUST include a validation entry for every issue in the list. Do not skip any.

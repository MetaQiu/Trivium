# Structure Guide - 论文结构指导

## Core Narrative Principle

Your paper is a story with ONE clear contribution supported by evidence.
Every section must serve this narrative. If a paragraph doesn't advance
the story, cut it.

**Three Pillars (must be crystal clear by end of introduction):**

| Pillar | Description |
|--------|-------------|
| **The What** | 1-3 specific novel claims within a cohesive theme |
| **The Why** | Rigorous empirical evidence supporting claims |
| **The So What** | Why readers should care, connection to recognized problems |

**If you cannot state your contribution in one sentence, the paper is not ready.**

## Section-Level Guidance

### Abstract (5-Sentence Formula)

1. What you achieved: "We introduce...", "We prove...", "We demonstrate..."
2. Why this is hard and important
3. How you do it (with specialist keywords for discoverability)
4. What evidence you have
5. Your most remarkable number/result

DELETE generic openings like "Large language models have achieved remarkable success..."

### Introduction (1-1.5 pages max)

Must include:
- Clear problem statement
- Brief approach overview
- 2-4 bullet contribution list (max 1-2 lines each)
- Methods should start by page 2-3 maximum

### Methods

Enable reimplementation:
- Conceptual outline or pseudocode
- All hyperparameters listed
- Architectural details sufficient for reproduction
- Present final design decisions; ablations go in experiments

### Experiments

For each experiment, explicitly state:
- What claim it supports
- How it connects to main contribution
- What to observe: "the blue line shows X, which demonstrates Y"
- Error bars with methodology
- Compute infrastructure (GPU type, total hours)

### Related Work

Organize methodologically, NOT paper-by-paper.

GOOD: "One line of work uses assumption A [refs] whereas we use assumption B because..."
BAD: "Smith et al. introduced X while Jones et al. introduced Y."

### Limitations (REQUIRED)

- Pre-empt criticisms by identifying weaknesses first
- Explain why limitations don't undermine core claims
- Honesty helps: reviewers are instructed not to penalize honest acknowledgment

## Paragraph-Level Rules

1. One paragraph = one core idea
2. Topic sentence first, then evidence, then analysis, then transition
3. Every claim must be supported by evidence or citation
4. No paragraph should exceed 8-10 sentences

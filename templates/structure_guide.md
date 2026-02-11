# Structure Guide - 论文结构指导

## Core Narrative Principle

Your paper is a story with ONE clear contribution supported by evidence.
Every section must serve this narrative. If a paragraph doesn't advance
the story, cut it.

> "A paper is a short, rigorous, evidence-based technical story with a takeaway readers care about." — Neel Nanda

> "A paper sells a single thing that was not obvious or present before. The entire paper is organized around this core contribution with surgical precision." — Andrej Karpathy

**Three Pillars (must be crystal clear by end of introduction):**

| Pillar | Description | Example |
|--------|-------------|---------|
| **The What** | 1-3 specific novel claims within a cohesive theme | "We prove that X achieves Y under condition Z" |
| **The Why** | Rigorous empirical evidence supporting claims | Strong baselines, experiments distinguishing hypotheses |
| **The So What** | Why readers should care, connection to recognized problems | Connection to recognized community problems |

**If you cannot state your contribution in one sentence, the paper is not ready.**

## Time Allocation

Spend approximately **equal time** on each of:
1. The abstract
2. The introduction
3. The figures
4. Everything else combined

Readers encounter your paper as: **title → abstract → introduction → figures → maybe the rest.** Most reviewers form judgments before reaching methods.

## Section-Level Guidance

### Abstract (5-Sentence Formula — Farquhar)

1. What you achieved: "We introduce...", "We prove...", "We demonstrate..."
2. Why this is hard and important
3. How you do it (with specialist keywords for discoverability)
4. What evidence you have
5. Your most remarkable number/result

DELETE generic openings like "Large language models have achieved remarkable success..."
If the first sentence can be prepended to any ML paper, delete it. Start with YOUR specific contribution.

**Good Example:**

> We prove that gradient descent on overparameterized neural networks converges to global minima at a linear rate. This resolves a fundamental question about why deep learning works despite non-convex optimization landscapes. Our proof relies on showing that the Neural Tangent Kernel remains approximately constant during training, reducing the problem to kernel regression. We validate our theory on CIFAR-10 and ImageNet, showing that predicted convergence rates match experiments within 5%. This is the first polynomial-time convergence guarantee for networks with practical depth and width.

### Introduction (1-1.5 pages max)

Structure template:

1. **Opening Hook** (2-3 sentences) — State the problem, why it matters RIGHT NOW
2. **Background/Challenge** (1 paragraph) — What makes this hard? What have others tried? Why is it insufficient?
3. **Your Approach** (1 paragraph) — What do you do differently? Key insight that enables your contribution
4. **Contribution Bullets** (2-4 items) — Be specific and falsifiable, max 1-2 lines each
5. **Results Preview** (2-3 sentences) — Most impressive numbers, scope of evaluation

Must include:
- Clear problem statement
- Brief approach overview
- 2-4 bullet contribution list (max 1-2 lines each)
- Methods should start by page 2-3 maximum

**Good contributions:**
- "We prove that X converges in O(n log n) time under assumption Y"
- "We introduce Z, a 3-layer architecture that reduces memory by 40%"

**Bad contributions:**
- "We study the problem of X" (not a contribution)
- "We provide extensive experiments" (too vague)

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
- Error bars with methodology (standard deviation vs standard error)
- Compute infrastructure (GPU type, total hours)
- Hyperparameter search ranges

### Related Work

Organize methodologically, NOT paper-by-paper.

GOOD: "One line of work uses assumption A [refs] whereas we use assumption B because..."
BAD: "Smith et al. introduced X while Jones et al. introduced Y."

Cite generously — reviewers likely authored relevant papers.

### Limitations (REQUIRED)

- Pre-empt criticisms by identifying weaknesses first
- Explain why limitations don't undermine core claims
- Honesty helps: reviewers are instructed not to penalize honest acknowledgment

## Sentence-Level Clarity — Gopen & Swan 7 Principles

These principles are based on how readers actually process prose. Violating them forces readers to spend cognitive effort on structure rather than content.

### Principle 1: Subject-Verb Proximity

Keep grammatical subject and verb close. Anything intervening reads as interruption.

- BAD: "The model, which was trained on 100M tokens and fine-tuned on domain-specific data using LoRA with rank 16, achieves state-of-the-art results"
- GOOD: "The model achieves state-of-the-art results after training on 100M tokens and fine-tuning with LoRA (rank 16)"

### Principle 2: Stress Position (Save the Best for Last)

Readers naturally emphasize the last words of a sentence. Place your most important information there.

- BAD: "Accuracy improves by 15% when using attention"
- GOOD: "When using attention, accuracy improves by 15%"

### Principle 3: Topic Position (First Things First)

The beginning of a sentence establishes perspective. Put context first, new info after.

- BAD: "A novel attention mechanism that computes alignment scores is introduced"
- GOOD: "To address the alignment problem, we introduce a novel attention mechanism"

### Principle 4: Old Information Before New

Put familiar information first for backward linkage; put new information at the end for emphasis.

- BAD: "Sparse attention was introduced by Child et al. The quadratic complexity of standard attention motivates this work."
- GOOD: "Standard attention has quadratic complexity. To address this, Child et al. introduced sparse attention."

### Principle 5: One Unit, One Function

Each unit of discourse (sentence, paragraph, section) should serve a single function. Two points need two units.

### Principle 6: Action in the Verb

Express the action of each sentence in its verb, not in nominalized nouns.

- BAD: "We performed an analysis of the results" (nominalization)
- GOOD: "We analyzed the results" (action in verb)

### Principle 7: Context Before New Information

Provide context before asking the reader to consider anything new.

- BAD: "Equation 3 shows that convergence is guaranteed when the learning rate satisfies..."
- GOOD: "For convergence to be guaranteed, the learning rate must satisfy the condition in Equation 3..."

| # | Rule | Mnemonic |
|---|------|----------|
| 1 | Keep subject and verb close | "Don't interrupt yourself" |
| 2 | Emphasis at sentence end | "Save the best for last" |
| 3 | Context at sentence start | "First things first" |
| 4 | Familiar → unfamiliar | "Build on known ground" |
| 5 | Each paragraph = one point | "One idea per container" |
| 6 | Use verbs, not nominalizations | "Verbs do, nouns sit" |
| 7 | Explain before presenting | "Set the stage first" |

## Word Choice & Precision

### Eliminate Hedging (Lipton)

Delete "may" and "can" unless genuinely uncertain. Remove vacuous intensifiers:
- Delete: very, extremely, highly, significantly (unless statistical)
- "provides *very* tight approximation" → "provides tight approximation"

### Be Specific (Steinhardt)

| Vague | Specific |
|-------|----------|
| performance | accuracy, latency, throughput |
| improves | increases accuracy by X%, reduces latency by Y |
| large | 1B parameters, 100M tokens |
| fast | 3x faster, 50ms latency |
| good results | 92% accuracy, 0.85 F1 |

### Consistent Terminology

Referring to the same concept with different terms creates confusion. Choose one and stick with it:
- "model" vs "network" vs "architecture" — pick one
- "training" vs "learning" vs "optimization" — pick one
- "sample" vs "example" vs "instance" — pick one

### Vocabulary Signaling

Avoid words signaling incremental work:
- Never: "combine," "modify," "expand," "extend"
- Instead: "develop," "propose," "introduce"

"We combine X and Y" sounds like stapling two existing ideas together.
"We develop a method that leverages X for Y" sounds like genuine contribution.

## Micro-Level Writing Tips (Perez)

### Pronoun Management

Minimize pronouns ("this," "it," "these"). When necessary, use them as adjectives with a noun:
- BAD: "This shows that the model converges."
- GOOD: "This result shows that the model converges."

### Verb Placement

Position verbs early in sentences:
- BAD: "The gradient, after being computed and normalized, updates the weights."
- GOOD: "The gradient updates the weights after being computed and normalized."

### Words to Eliminate

Delete in almost all cases: "actually," "a bit," "fortunately," "unfortunately," "very," "really," "quite," "basically," "essentially"

### Filler Phrase Replacements

- "In order to" → "To"
- "Due to the fact that" → "Because"
- "It is worth noting that" → (delete, state the point directly)
- "A number of" → "Several" or the exact number
- "In the context of" → "In" or "For"

## Figure Design

- **Figure 1 is crucial**: Often the first thing readers examine after abstract
- Use vector graphics (PDF/EPS for plots). Raster (PNG 600 DPI) only for photographs
- Captions must be self-contained — reader should understand without main text
- No title inside figure — the caption serves this function
- Use colorblind-safe palettes (Okabe-Ito or Paul Tol). Avoid red-green combinations
- Verify grayscale readability (8% of men have color vision deficiency)

## Paragraph-Level Rules

1. One paragraph = one core idea
2. Topic sentence first, then evidence, then analysis, then transition
3. Every claim must be supported by evidence or citation
4. No paragraph should exceed 8-10 sentences
5. First sentence states the point clearly; last sentence reinforces or transitions
6. Do not bury key information in the middle of paragraphs

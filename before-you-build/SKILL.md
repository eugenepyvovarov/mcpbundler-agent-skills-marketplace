---
name: before-you-build
description: Use before building or changing a product, feature, SaaS, AI app, side project, or startup idea to run a short demand, distribution, and failure-pattern reality check.
---

# before-you-build

Don't ask AI to build it yet. Ask why it might fail first.

## Purpose

Use this skill before implementation planning when the user wants to build a new product, add a feature, change requirements, expand scope, or pivot direction.

The goal is to help the user avoid building the wrong thing faster.

## Hard Gate

Do not write code.

Do not scaffold a project.

Do not recommend a tech stack.

Do not create an implementation plan yet.

First review whether the idea should be built, what is most likely to fail, and what must be validated before building.

## Triggers

Use this skill when the user says things like:

- "Is this worth building?"
- "Should I add this feature?"
- "Will anyone want this?"
- "Sanity-check this product idea."
- "The requirements changed. Should we still implement this?"
- "Pour cold water on this idea before coding starts."

## Interaction

If the idea is too broad, ask one clarification:

```text
This idea is too broad for a responsible review.

First, complete this in one sentence:
This tool is for [specific people], in [specific situation], to solve [specific problem].
```

If the current alternative is missing and the review would be too speculative, ask one more question:

```text
How do they solve this today, and why is that not good enough?
```

Ask at most two questions before giving a constrained review.

## Output

Use this default structure:

```markdown
## Quick Reality Check

Assumption:
- [State the assumption if any.]

Verdict:
- Don't build yet / Build smaller / Build only if / Build small

Biggest risk:
- [The most important likely failure mode.]

Most likely problem:
- [Demand / distribution / pricing / positioning / retention / trust.]

What to validate first:
- [One concrete test before implementation.]

Smallest useful version:
- [A narrower version worth testing.]
```

## Evidence Rules

Weak signals:

- friends saying it sounds useful;
- social likes;
- generic survey interest;
- a competitor existing;
- the builder personally wanting it.

Stronger signals:

- users already paying for a workaround;
- repeated complaints in specific communities;
- manual workflows that waste real time or money;
- signed pilots, preorders, migration attempts, or repeated usage.

Full project:
https://github.com/bin1874/before-you-build-skill

---
name: code-review
description: Two-stage code review checking spec compliance then code quality. Use when a dev-builder Task is complete and before commit.
intent: Independent reviewer for spec compliance Stage 1 and code quality Stage 2. Stage 1 failures are blocking. Output is gated by exit-check.py to prevent leniency bias.
type: interactive
---

## Purpose

Perform an independent two-stage code review. This is a reasoning sensor. Stage 1 checks spec compliance. Stage 2 checks code quality. Stage 1 is blocking.

## Key Concepts

- Independent reviewer mindset - you did not write this code
- Spec as acceptance checklist - verify each requirement in L2-spec.md
- Design mockup as visual contract - UI code must match the mockup

### Anti-Patterns
- Not a praise session
- Not a syntax linter - focus on logic and architecture
- Not a rubber


## Application

### Stage 1 - Spec Compliance
1. Identify relevant spec items in L2-spec.md and design mockup.
2. Check each item: Fully Implemented / Partially / Missing / Extra Scope.
3. Classify issues: HIGH (blocking), MEDIUM, LOW.
4. If any HIGH issues exist, stop here. Do not proceed to Stage 2.

### Stage 2 - Code Quality
Check type safety, naming, structure, security, and error handling.
Skip this stage if Stage 1 has HIGH issues.

### Output Format
Write your review with:
- Stage 1 summary with checklist
- HIGH issues list (if any)
- Stage 2 summary (if reached)
- Approval status: Approve / Revise and re-submit

## Examples

### Good Review
Finds a missing validation rule and marks it HIGH.
Lists a naming inconsistency in Stage 2.

### Bad Review
Says looks good with no actionable issues.

## Spec Gap Protocol (G3b)

When implementation discovers that L2-spec is ambiguous or missing requirements, classify the gap and follow the corresponding decision path:

| Type | Description | Decision Maker | Action |
|------|-----------|---------------|--------|
| **A** | Feature in spec but description insufficient | PM | Document completion → update L2-spec |
| **B** | Spec text exists but meaning ambiguous | PM + Designer | Joint interpretation → update L2-spec |
| **C (small)** | Missing requirement, impact < 20% story points | PM | Absorb within OKR → update spec and plan |
| **C (large)** | Missing requirement, impact ≥ 20% story points | PM → Leadership | Escalate to leadership |
| **D** | Strategic direction change needed during implementation | PM → Leadership | Escalate with recommendation |
| **E** | Discovery contradicts spec assumption | PM | Re-evaluate spec → update or pivot |

### Spec Gap Recording Format

Record all gaps in L4-plan.md under "Spec Gaps" section:

```markdown
### GAP-001: {brief description}
- **Type**: A/B/C/D/E
- **Discovered by**: {Agent/Role}
- **Discovered at**: {Phase/Task}
- **Decision**: {decision content}
- **Impact**: {scope of impact}
- **Status**: Open/Resolved/Deferred
```

### Reviewer Responsibilities During Spec Gaps

1. **Classify** the gap type (A-E) based on the table above
2. **Record** the gap in L4-plan.md "Spec Gaps" section
3. **Pause** implementation for type C(large), D, E — request PM decision before continuing
4. **Continue** for type A, B, C(small) — document the gap and the assumed interpretation, flag for PM review

### Common Pitfalls

### Pitfall 1: Leniency Bias
**Symptom:** The code looks good overall. Just a small nitpick.
**Fix:** Always find at least one issue or structural suggestion.

### Pitfall 2: Skipping Design Comparison
**Symptom:** Reviewing UI code without looking at the mockup.
**Fix:** Always compare UI code to mockups.

### Pitfall 3: Stage 1 HIGH Issues But Proceeding to Stage 2
**Symptom:** Noticing a missing feature but still checking code quality.
**Fix:** Stop at Stage 1. Mark it blocking.

### Pitfall 4: Ignoring Scope Creep
**Symptom:** Implementation adds features not in spec, reviewer doesn't flag it.
**Fix:** Flag every feature not traceable to a spec item. Classify as Spec Gap type A-E.

### Pitfall 5: Missing User Impact on HIGH Issues
**Symptom:** Marking an issue as HIGH without explaining who it affects.
**Fix:** Every HIGH issue must include user impact assessment for PM decision.

## References

### Related Skills
- dev-builder — Produces the code this Skill reviews
- bug-fixer — Called when review finds defects
- dev-planner — Provides the Task boundaries

### External Frameworks
- Google Code Review Practices
- Marty Cagan, Inspired (Minimum Viable Product)

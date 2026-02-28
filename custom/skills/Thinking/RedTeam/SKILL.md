---
name: RedTeam
description: Adversarial analysis framework with structured attack vectors. USE WHEN user says "red team", "attack this", "find flaws", "what could go wrong", "stress test", or needs to find vulnerabilities in an idea, design, or plan.
---

# RedTeam — Adversarial Analysis Framework

Systematically attack ideas, designs, and plans from multiple adversarial angles to find weaknesses before they become problems.

## Philosophy

See `Philosophy.md` for the adversarial mindset.

## Attack Vector Categories

| Category | Focus | Example Questions |
|----------|-------|-------------------|
| 🔓 Security | Auth, injection, data leaks | "How could an attacker exploit this?" |
| 💥 Reliability | Failure modes, edge cases | "What happens when X fails?" |
| 📈 Scale | Load, data growth, limits | "What breaks at 100x traffic?" |
| 🧩 Complexity | Maintenance, cognitive load | "Can a new dev understand this?" |
| 💰 Cost | Resource usage, hidden costs | "What's the unexpected bill?" |
| 🔄 Integration | Dependencies, API contracts | "What if upstream changes?" |
| 👤 Human | Misuse, confusion, social eng | "How will users misuse this?" |
| ⏰ Time | Race conditions, ordering | "What if events arrive out of order?" |

## Workflows

- **ParallelAnalysis** (`ParallelAnalysis.md`): Analyze across all vectors simultaneously
- **AdversarialValidation** (`AdversarialValidation.md`): Deep-dive on specific attack vectors

## Output Format

For each vulnerability found:
```
### [Severity: 🔴 Critical / 🟡 Medium / 🟢 Low]
**Vector:** [category]
**Attack:** [how to exploit]
**Impact:** [what goes wrong]
**Mitigation:** [how to fix]
**Effort:** [fix difficulty]
```

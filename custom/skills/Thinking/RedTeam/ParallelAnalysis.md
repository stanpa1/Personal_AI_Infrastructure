# ParallelAnalysis Workflow

Rapid assessment across all attack vector categories.

## Trigger
User says "red team this", "find flaws", "what could go wrong"

## Steps

1. **Understand the target** — Summarize what's being analyzed
2. **Parallel sweep** — For each of the 8 categories, identify the top threat
3. **Severity ranking** — Sort findings by severity
4. **Mitigation map** — Suggest fixes for Critical and Medium findings

## Output Format

```
# RedTeam Analysis: [Target]

## Target Summary
[1-2 sentences describing what's being analyzed]

## Findings

| # | Severity | Vector | Threat | Mitigation |
|---|----------|--------|--------|------------|
| 1 | 🔴 | ... | ... | ... |
| 2 | 🟡 | ... | ... | ... |
| ... | ... | ... | ... | ... |

## Critical Action Items
1. [Most urgent fix]
2. [Second most urgent]

## Accepted Risks
- [Low-severity items with justification]
```

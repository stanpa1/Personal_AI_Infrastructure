# StructuredInvestigation Workflow

Multi-hypothesis investigation with systematic evidence gathering.

## Trigger
User says "investigate", "figure out why", "something weird is happening"

## Steps

1. **Observe thoroughly** — Gather all available evidence
2. **Generate hypotheses** — At least 4, including null hypothesis
3. **Rank by testability** — Which can be tested fastest/cheapest?
4. **Design experiments** — One per hypothesis
5. **Execute & record** — Test systematically, log everything
6. **Analyze** — Which hypotheses survived?
7. **Conclude** — State finding with confidence level

## Output Format

```
# 🔬 Investigation: [Topic]

## Evidence Gathered
1. [observation]
2. [observation]
...

## Hypotheses
| # | Hypothesis | Prior Probability | Testability |
|---|-----------|-------------------|-------------|
| H0 | [null: nothing unusual] | ... | ... |
| H1 | [explanation 1] | ... | ... |
| H2 | [explanation 2] | ... | ... |
| H3 | [explanation 3] | ... | ... |

## Experiments & Results
### Test for H1
[experiment template filled in]

### Test for H2
[experiment template filled in]

## Conclusion
**Finding:** [what we determined]
**Confidence:** [High/Medium/Low]
**Remaining uncertainty:** [what we still don't know]
**Next steps:** [if further investigation needed]
```

# AdversarialValidation Workflow

Deep-dive adversarial analysis on specific vectors.

## Trigger
User specifies particular concern areas, or ParallelAnalysis found Critical issues

## Steps

1. **Select vectors** — Pick 2-3 most relevant attack categories
2. **Deep attack** — For each vector, explore attack chains (3+ steps)
3. **Proof of concept** — Describe concrete exploitation scenario
4. **Defense design** — Propose layered mitigations
5. **Residual risk** — What remains even after mitigations

## Output Format

For each selected vector:
```
## [Vector Name] — Deep Analysis

### Attack Chain
1. [Step 1] → [Step 2] → [Step 3] → [Impact]

### Exploitation Scenario
[Concrete narrative of how an attacker would exploit this]

### Layered Defense
1. **Prevention:** [stop the attack]
2. **Detection:** [notice if it happens]
3. **Response:** [limit damage]

### Residual Risk
[What's still possible even with mitigations]
```

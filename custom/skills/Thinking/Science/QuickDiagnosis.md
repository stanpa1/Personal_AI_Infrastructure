# QuickDiagnosis Workflow

Rapid hypothesis testing for bugs and issues.

## Trigger
User says "debug this", "why is this happening", "diagnose"

## Steps

1. **Observe** — What's the symptom? What's expected vs actual?
2. **Quick hypotheses** — List 3 most likely causes
3. **Fastest test** — Which hypothesis can be tested quickest?
4. **Test & eliminate** — Run test, eliminate or confirm
5. **Repeat** — Until root cause found

## Output Format

```
# 🔬 Quick Diagnosis: [Symptom]

## Observation
- **Expected:** [what should happen]
- **Actual:** [what's happening]
- **Context:** [when/where it occurs]

## Hypotheses (ordered by likelihood)
1. **H1:** [most likely cause]
   - Test: [how to verify]
2. **H2:** [second most likely]
   - Test: [how to verify]
3. **H3:** [third option]
   - Test: [how to verify]

## Investigation
[Test results as they come in]

## Root Cause
**[confirmed hypothesis]** because [evidence]

## Fix
[recommended solution]
```

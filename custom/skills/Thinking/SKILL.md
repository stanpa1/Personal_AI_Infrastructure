---
name: Thinking
description: Router for structured thinking frameworks. USE WHEN user says "think deeply", "analyze this", "debate this", "red team", "council", "first principles", "be creative", "brainstorm", "scientific method", "investigate", or requests rigorous multi-perspective analysis.
---

# Thinking Skills Router

Structured thinking frameworks for deep analysis, creative exploration, and rigorous problem-solving.

## Available Frameworks

| Keyword | Skill | Best For |
|---------|-------|----------|
| `council`, `debate` | **Council** | Multi-perspective decisions, architecture choices |
| `red team`, `attack`, `vulnerabilities` | **RedTeam** | Security review, finding flaws, stress-testing ideas |
| `first principles`, `fundamentals` | **FirstPrinciples** | Breaking down complex problems, challenging assumptions |
| `creative`, `brainstorm`, `ideas` | **BeCreative** | Generating novel solutions, creative exploration |
| `deep analysis`, `lenses`, `hidden` | **IterativeDepth** | Finding hidden requirements, thorough analysis |
| `scientific`, `hypothesis`, `investigate` | **Science** | Debugging, root cause analysis, systematic investigation |

## Routing Rules

1. Match user intent to the most relevant framework
2. If unclear, ask which framework to use
3. Multiple frameworks can be combined (e.g., FirstPrinciples → Council → RedTeam)

## Quick Start

```
"Use council to debate whether we should use microservices"
→ Loads Council/SKILL.md, runs Debate workflow

"Red team this authentication design"
→ Loads RedTeam/SKILL.md, runs ParallelAnalysis workflow

"Think about this from first principles"
→ Loads FirstPrinciples/SKILL.md, runs Deconstruct → Challenge → Reconstruct

"Be creative about solving the caching problem"
→ Loads BeCreative/SKILL.md, runs StandardCreativity workflow

"Analyze this deeply - what am I missing?"
→ Loads IterativeDepth/SKILL.md, runs 8-lens Explore workflow

"Investigate why the tests are flaky"
→ Loads Science/SKILL.md, runs QuickDiagnosis workflow
```

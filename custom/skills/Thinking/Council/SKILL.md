---
name: Council
description: Multi-agent structured debate. 4 agents argue through 3 rounds to find the best solution. USE WHEN user says "council", "debate", "discuss from multiple angles", or needs a decision with competing trade-offs.
---

# Council — Multi-Agent Debate Framework

Four specialized agents debate a problem through 3 structured rounds, converging on a well-tested recommendation.

## Council Members

See `CouncilMembers.md` for detailed role descriptions.

| Agent | Focus | Optimizes For |
|-------|-------|---------------|
| 🏗️ Architect | System design, scalability | Long-term maintainability |
| 🎨 Designer | User experience, simplicity | Elegance and usability |
| ⚙️ Engineer | Implementation, performance | Practical feasibility |
| 🔬 Researcher | Evidence, precedent | Data-driven decisions |

## Workflows

- **Debate** (`Debate.md`): Full 3-round debate with opening statements, challenges, and synthesis
- **Quick** (`Quick.md`): Single-round quick assessment from all 4 perspectives

## How to Use

1. State the problem or decision clearly
2. Each agent gives their opening position (Round 1)
3. Agents challenge each other's positions (Round 2)
4. Synthesis and final recommendation (Round 3)

## Output

See `OutputFormat.md` for the standard output structure.

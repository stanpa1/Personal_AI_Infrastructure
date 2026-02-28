// ~/.claude/hooks/lib/paths.ts
// Path utilities for PAI hooks

import { homedir } from "os";
import { join } from "path";

export function getPAIDir(): string {
  return process.env.PAI_DIR || join(homedir(), ".claude");
}

export function getMemoryDir(): string {
  return join(getPAIDir(), "MEMORY");
}

export function getLearningDir(): string {
  return join(getMemoryDir(), "learnings");
}

export function getSignalsDir(): string {
  return join(getLearningDir(), "signals");
}

export function getFailuresDir(): string {
  return join(getLearningDir(), "failures");
}

export function getSessionsDir(): string {
  return join(getMemoryDir(), "sessions");
}

export function getSkillsDir(): string {
  return join(getPAIDir(), "skills");
}

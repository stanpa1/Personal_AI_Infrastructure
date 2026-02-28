#!/usr/bin/env bun
// ~/.claude/hooks/session-learning.ts
// Stop hook: Captures a brief session log when Claude Code exits
// Writes structured data to ~/.claude/MEMORY/sessions/

import { readStdin, exitSilent } from "./lib/hook-io";
import { getSessionsDir } from "./lib/paths";
import { getISOTimestamp, getDateTimeSlug } from "./lib/time";
import { mkdirSync, writeFileSync } from "fs";
import { join } from "path";

interface StopPayload {
  session_id?: string;
  stop_hook_active?: boolean;
  [key: string]: any;
}

interface SessionLog {
  timestamp: string;
  session_id: string;
  raw_payload: Record<string, any>;
}

async function main() {
  const payload = await readStdin<StopPayload>();

  const sessionsDir = getSessionsDir();
  mkdirSync(sessionsDir, { recursive: true });

  const slug = getDateTimeSlug();
  const sessionId = payload?.session_id || "unknown";

  const log: SessionLog = {
    timestamp: getISOTimestamp(),
    session_id: sessionId,
    raw_payload: payload || {},
  };

  const logFile = join(sessionsDir, `session-${slug}-${sessionId.slice(0, 8)}.json`);
  writeFileSync(logFile, JSON.stringify(log, null, 2));

  exitSilent();
}

main();

#!/usr/bin/env bun
// ~/.claude/hooks/rating-capture.ts
// UserPromptSubmit hook: Capture explicit ratings from user prompts
// Detects patterns like "8/10", "rating: 7", "ocena: 9"

import { readStdin, exitSilent } from "./lib/hook-io";
import { getSignalsDir, getFailuresDir } from "./lib/paths";
import { getISOTimestamp, getDateSlug } from "./lib/time";
import { mkdirSync, appendFileSync, writeFileSync } from "fs";
import { join } from "path";

interface UserPromptPayload {
  session_id: string;
  prompt?: string;
  message?: string;
  [key: string]: any;
}

interface RatingEntry {
  timestamp: string;
  session_id: string;
  rating: number;
  max: number;
  context: string;
  prompt_excerpt: string;
}

// Match explicit rating patterns
const RATING_PATTERNS = [
  /(\d{1,2})\s*\/\s*10/i,                          // 8/10
  /(\d{1,2})\s*\/\s*5/i,                            // 4/5
  /(?:rating|ocena|nota|score)\s*[:=]?\s*(\d{1,2})/i,  // rating: 7, ocena: 9
  /(\d{1,2})\s*(?:out of|z)\s*(\d{1,2})/i,         // 8 out of 10, 8 z 10
];

function extractRating(text: string): { rating: number; max: number } | null {
  for (const pattern of RATING_PATTERNS) {
    const match = text.match(pattern);
    if (!match) continue;

    const rating = parseInt(match[1]);

    // Determine max based on pattern
    if (pattern.source.includes("\\/\\s*10")) {
      if (rating >= 0 && rating <= 10) return { rating, max: 10 };
    } else if (pattern.source.includes("\\/\\s*5")) {
      if (rating >= 0 && rating <= 5) return { rating, max: 5 };
    } else if (match[2]) {
      const max = parseInt(match[2]);
      if (rating >= 0 && rating <= max && max <= 10) return { rating, max };
    } else {
      // Default: assume out of 10
      if (rating >= 0 && rating <= 10) return { rating, max: 10 };
    }
  }
  return null;
}

async function main() {
  const payload = await readStdin<UserPromptPayload>();
  if (!payload) exitSilent();

  const prompt = payload!.prompt || payload!.message || "";
  if (!prompt || prompt.length < 2) exitSilent();

  const result = extractRating(prompt);
  if (!result) exitSilent();

  const signalsDir = getSignalsDir();
  mkdirSync(signalsDir, { recursive: true });

  const entry: RatingEntry = {
    timestamp: getISOTimestamp(),
    session_id: payload!.session_id || "unknown",
    rating: result.rating,
    max: result.max,
    context: prompt.slice(0, 500),
    prompt_excerpt: prompt.slice(0, 200),
  };

  // Append to ratings JSONL
  const ratingsFile = join(signalsDir, "ratings.jsonl");
  appendFileSync(ratingsFile, JSON.stringify(entry) + "\n");

  // For low ratings (≤3 on /10 scale, or ≤1 on /5 scale), capture failure context
  const normalizedRating = (result.rating / result.max) * 10;
  if (normalizedRating <= 3) {
    const failuresDir = getFailuresDir();
    mkdirSync(failuresDir, { recursive: true });

    const slug = getDateSlug();
    const failureFile = join(failuresDir, `failure-${slug}-${Date.now()}.json`);
    writeFileSync(failureFile, JSON.stringify({
      ...entry,
      full_prompt: prompt,
      severity: normalizedRating <= 2 ? "critical" : "low",
    }, null, 2));
  }

  exitSilent();
}

main();

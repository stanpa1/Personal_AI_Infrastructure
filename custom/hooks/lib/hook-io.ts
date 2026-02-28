// ~/.claude/hooks/lib/hook-io.ts
// Standard I/O utilities for Claude Code hooks

export async function readStdin<T = Record<string, any>>(): Promise<T | null> {
  try {
    const data = await Bun.stdin.text();
    if (!data.trim()) return null;
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
}

export function exitOk(message?: string): never {
  if (message) {
    // Output message back to Claude via stdout
    console.log(JSON.stringify({ message }));
  }
  process.exit(0);
}

export function exitBlock(reason: string): never {
  console.error(`[HOOK BLOCKED] ${reason}`);
  process.exit(1);
}

export function exitSilent(): never {
  process.exit(0);
}

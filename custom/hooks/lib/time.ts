// ~/.claude/hooks/lib/time.ts
// Time utilities for PAI hooks — uses Europe/Warsaw timezone

const TIMEZONE = process.env.TIME_ZONE || "Europe/Warsaw";

export function getISOTimestamp(): string {
  return new Date().toISOString();
}

export function getLocalTime(): string {
  return new Date().toLocaleString("pl-PL", { timeZone: TIMEZONE });
}

export function getDateSlug(): string {
  const now = new Date();
  const year = now.toLocaleString("en", { timeZone: TIMEZONE, year: "numeric" });
  const month = now.toLocaleString("en", { timeZone: TIMEZONE, month: "2-digit" });
  return `${year}-${month}`;
}

export function getDateTimeSlug(): string {
  const now = new Date();
  const opts: Intl.DateTimeFormatOptions = { timeZone: TIMEZONE };
  const year = now.toLocaleString("en", { ...opts, year: "numeric" });
  const month = now.toLocaleString("en", { ...opts, month: "2-digit" });
  const day = now.toLocaleString("en", { ...opts, day: "2-digit" });
  const hour = now.toLocaleString("en", { ...opts, hour: "2-digit", hour12: false });
  const minute = now.toLocaleString("en", { ...opts, minute: "2-digit" });
  return `${year}-${month}-${day}_${hour}${minute}`;
}

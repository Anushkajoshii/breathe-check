import type { Category } from "./data";

/** 0 -> "midnight", 12 -> "noon", 14 -> "2 pm" */
export function hourLabel(h: number): string {
  const hh = ((h % 24) + 24) % 24;
  if (hh === 0) return "midnight";
  if (hh === 12) return "noon";
  return `${hh % 12} ${hh < 12 ? "am" : "pm"}`;
}

/** 12, 14 -> "noon to 2 pm" */
export function windowLabel(start: number, end: number): string {
  return `${hourLabel(start)} to ${hourLabel(end)}`;
}

export type Level = "good" | "warning" | "serious" | "critical";

/** India's AQI categories grouped into four plain levels, each shown with an icon and words. */
export function levelOf(category: Category): Level {
  switch (category) {
    case "Good":
    case "Satisfactory":
      return "good";
    case "Moderate":
      return "warning";
    case "Poor":
      return "serious";
    default:
      return "critical";
  }
}

export function cigarettesText(n: number): string {
  if (n < 0.5) return "less than half a cigarette";
  const rounded = Math.round(n * 10) / 10;
  return `about ${rounded} cigarette${rounded === 1 ? "" : "s"}`;
}

/** "2026-11-29" -> "Sunday 29 November" */
export function dayLabel(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00`);
  return d.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });
}

/** How old a timestamp is, in plain words. */
export function ago(iso: string, now: Date = new Date()): string {
  const then = new Date(iso.includes("T") ? iso : iso.replace(" ", "T"));
  const hours = Math.round((now.getTime() - then.getTime()) / 3_600_000);
  if (hours < 1) return "less than an hour ago";
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

export const WHO_DAILY = 15;
export const INDIA_DAILY = 60;

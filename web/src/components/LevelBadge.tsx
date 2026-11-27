import type { Category } from "../data";
import { levelOf } from "../format";

const ICON: Record<string, string> = {
  good: "M5 12.5l4 4 10-10", // tick
  warning: "M12 7v6 M12 17h.01", // exclamation
  serious: "M12 7v6 M12 17h.01",
  critical: "M7 7l10 10 M17 7L7 17", // cross
};

/** A category always shows as icon + words, never colour alone. */
export function LevelBadge({ category }: { category: Category }) {
  const level = levelOf(category);
  return (
    <span className={`badge badge-${level}`}>
      <svg viewBox="0 0 24 24" aria-hidden="true" width="14" height="14">
        <path d={ICON[level]} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {category}
    </span>
  );
}

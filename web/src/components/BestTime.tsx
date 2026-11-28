import type { ReactNode } from "react";
import type { Category, Forecast } from "../data";
import { dayLabel, hourLabel, levelOf, windowLabel } from "../format";
import { IconClock, IconLungs, IconTrendUp } from "./Icons";
import { LevelBadge } from "./LevelBadge";

const HEADLINE: Record<string, string> = {
  good: "A good window to head out",
  warning: "Okay for most, keep it short if you're sensitive",
  serious: "Choose indoor exercise if you can",
  critical: "Best to stay indoors tomorrow",
};

export function BestTime({ f }: { f: Forecast }) {
  const best = f.best_window;
  if (!best) {
    return (
      <section className="card hero">
        <p className="eyebrow">Tomorrow in {f.name}</p>
        <p>There isn't enough forecast data for {f.name} tomorrow yet. Check back after 7 pm.</p>
      </section>
    );
  }
  const level = levelOf(best.category);
  const worst = f.hours.find((h) => h.hour === f.worst_hour);
  return (
    <section className={`card hero hero-${level}`} aria-labelledby="best-title">
      <p className="eyebrow">
        Tomorrow in {f.name} · {dayLabel(f.for_date)}
      </p>
      <p className="hero-kicker">Best time to be outside</p>
      <h2 id="best-title" className="hero-time">
        {windowLabel(best.start, best.end)}
      </h2>
      <p className="hero-headline">{HEADLINE[level]}</p>
      <p className="hero-advice">{best.advice}</p>

      <div className="tiles">
        <Tile icon={<IconClock />} label="PM2.5 in the window">
          <strong>{Math.round(best.pm25)}</strong> µg/m³ <LevelBadge category={best.category} />
        </Tile>
        {worst && (
          <Tile icon={<IconTrendUp />} label="Worst hour">
            <strong>{hourLabel(worst.hour)}</strong>
            {`, about ${Math.round(worst.mid)} µg/m³ `}
            <LevelBadge category={worst.category as Category} />
          </Tile>
        )}
        {f.today && (
          <Tile icon={<IconLungs />} label="Last 24 hours">
            <strong>{Math.round(f.today.pm25)}</strong>
            {` µg/m³ · ≈ ${f.today.cigarettes.toFixed(1)} cigarettes a day`}
          </Tile>
        )}
      </div>
    </section>
  );
}

function Tile({ icon, label, children }: { icon: ReactNode; label: string; children: ReactNode }) {
  return (
    <div className="tile">
      <span className="tile-icon">{icon}</span>
      <span className="tile-label">{label}</span>
      <span className="tile-value">{children}</span>
    </div>
  );
}

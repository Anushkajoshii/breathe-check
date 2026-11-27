import type { Forecast } from "../data";
import { dayLabel, hourLabel, windowLabel } from "../format";
import { LevelBadge } from "./LevelBadge";

export function BestTime({ f }: { f: Forecast }) {
  const best = f.best_window;
  if (!best) {
    return (
      <section className="card hero">
        <p className="eyebrow">Tomorrow, {dayLabel(f.for_date)}</p>
        <p>There isn't enough forecast data for {f.name} tomorrow yet.</p>
      </section>
    );
  }
  const worst = f.hours.find((h) => h.hour === f.worst_hour);
  return (
    <section className="card hero" aria-labelledby="best-title">
      <p className="eyebrow">Best time to be outside tomorrow, {dayLabel(f.for_date)}</p>
      <h2 id="best-title" className="hero-time">
        {windowLabel(best.start, best.end)}
      </h2>
      <p className="hero-line">
        About <strong>{Math.round(best.pm25)} µg/m³</strong> of PM2.5 <LevelBadge category={best.category} />
      </p>
      <p className="muted">{best.advice}</p>
      {worst && worst.mid > best.pm25 * 1.2 && (
        <p className="muted small">
          Worst hour: around {hourLabel(worst.hour)}, about {Math.round(worst.mid)} µg/m³, which is{" "}
          {(worst.mid / best.pm25).toFixed(1)} times the best window.
        </p>
      )}
    </section>
  );
}

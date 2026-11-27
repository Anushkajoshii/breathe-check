import type { Forecast } from "../data";
import { ago, cigarettesText } from "../format";
import { LevelBadge } from "./LevelBadge";

function Cigarette({ fill }: { fill: number }) {
  // fill: 0..1, how much of this cigarette counts
  return (
    <svg viewBox="0 0 40 8" className="cig" aria-hidden="true">
      <rect x="0" y="1" width="40" height="6" rx="1" className="cig-empty" />
      <rect x="0" y="1" width={32 * fill} height="6" rx="1" className="cig-paper" />
      {fill > 0 && <rect x={32 * fill} y="1" width={Math.min(8, 40 - 32 * fill)} height="6" className="cig-filter" />}
    </svg>
  );
}

export function LastDay({ f }: { f: Forecast }) {
  const t = f.today;
  if (!t) return null;
  const whole = Math.floor(t.cigarettes);
  const part = t.cigarettes - whole;
  const shown = Math.min(whole, 12);
  return (
    <section className="card" aria-labelledby="lastday-title">
      <h3 id="lastday-title">The last 24 hours in {f.name}</h3>
      <p className="big-number">
        {Math.round(t.pm25)} <span className="unit">µg/m³</span> <LevelBadge category={t.aqi_category} />
      </p>
      <p>
        Breathing this air for a day is like smoking <strong>{cigarettesText(t.cigarettes)}</strong>.
      </p>
      <div className="cigs" role="img" aria-label={cigarettesText(t.cigarettes)}>
        {Array.from({ length: shown }, (_, i) => (
          <Cigarette key={i} fill={1} />
        ))}
        {part >= 0.1 && whole < 12 && <Cigarette fill={part} />}
      </div>
      <p className="muted small">
        {t.advice} Readings up to {ago(t.until)}. The cigarette comparison is Berkeley Earth's rough rule of thumb
        (22 µg/m³ for a day ≈ 1 cigarette), not a medical measure.
      </p>
    </section>
  );
}

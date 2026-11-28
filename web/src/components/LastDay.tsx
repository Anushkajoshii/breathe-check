import type { Forecast } from "../data";
import { ago, cigarettesText } from "../format";
import { IconLungs } from "./Icons";
import { LevelBadge } from "./LevelBadge";

function Cigarette({ fill }: { fill: number }) {
  return (
    <svg viewBox="0 0 48 10" className="cig" aria-hidden="true">
      <rect x="0.5" y="1.5" width="47" height="7" rx="2" className="cig-outline" />
      <rect x="0.5" y="1.5" width={38 * fill} height="7" rx="2" className="cig-paper" />
      {fill > 0 && <rect x={Math.min(38 * fill, 38)} y="1.5" width="9.5" height="7" rx="1.5" className="cig-filter" />}
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
      <div className="card-head">
        <span className="card-icon">
          <IconLungs />
        </span>
        <h3 id="lastday-title">The last 24 hours in {f.name}</h3>
      </div>
      <p className="big-number">
        {Math.round(t.pm25)} <span className="unit">µg/m³ average</span> <LevelBadge category={t.aqi_category} />
      </p>
      <p className="lead-line">
        Breathing this air for a full day is like smoking <strong>{cigarettesText(t.cigarettes)}</strong>.
      </p>
      <div className="cigs" role="img" aria-label={cigarettesText(t.cigarettes)}>
        {Array.from({ length: shown }, (_, i) => (
          <Cigarette key={i} fill={1} />
        ))}
        {part >= 0.1 && whole < 12 && <Cigarette fill={part} />}
      </div>
      <p className="muted small">
        {t.advice} Latest reading {ago(t.until)}. The cigarette comparison is Berkeley Earth's rule of thumb (22 µg/m³
        for a day ≈ 1 cigarette), a way to picture the number, not a medical measure.
      </p>
    </section>
  );
}

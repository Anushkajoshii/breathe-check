import type { Forecast } from "../data";

export function Smoke({ f }: { f: Forecast }) {
  const s = f.smoke;
  if (!s) return null;
  const tone = s.level === "Likely" ? "serious" : "neutral";
  return (
    <section className={`card smoke smoke-${tone}`} aria-labelledby="smoke-title">
      <h3 id="smoke-title">Crop-fire smoke tomorrow</h3>
      <p className="big-number small-big">{s.level}</p>
      <p className="muted">{s.why}</p>
      <p className="muted small">
        "Likely" means more than 1,500 fires in Punjab and Haryana and wind mostly from the north-west. On such days
        since 2018, Delhi averaged 252 µg/m³, against 143 on other October and November days.
      </p>
    </section>
  );
}

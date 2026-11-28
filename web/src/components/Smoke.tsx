import type { Forecast } from "../data";
import { IconFlame } from "./Icons";

export function Smoke({ f }: { f: Forecast }) {
  const s = f.smoke;
  if (!s) return null;
  const likely = s.level === "Likely";
  return (
    <section className={`card smoke ${likely ? "smoke-likely" : ""}`} aria-labelledby="smoke-title">
      <div className="card-head">
        <span className="card-icon">
          <IconFlame />
        </span>
        <h3 id="smoke-title">Crop-fire smoke tomorrow</h3>
      </div>
      <p className="big-number">{s.level}</p>
      <p className="lead-line">{s.why}</p>
      <p className="muted small">
        We call it "Likely" when satellites saw more than 1,500 fires in Punjab and Haryana and the wind is mostly from
        the north-west. On those days since 2018, Delhi averaged 252 µg/m³, against 143 on other October and November
        days.
      </p>
    </section>
  );
}

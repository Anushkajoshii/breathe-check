import { IconChart, IconRefresh, IconSatellite } from "./Icons";

const STEPS = [
  {
    icon: <IconSatellite />,
    title: "Real readings",
    text: "Hourly PM2.5 from 225 government (CPCB) monitors, weather from Open-Meteo and crop fires from NASA satellites.",
  },
  {
    icon: <IconChart />,
    title: "A weather-aware forecast",
    text: "Models learn how wind, mixing height and rain move pollution, then forecast every hour of tomorrow with an honest range.",
  },
  {
    icon: <IconRefresh />,
    title: "Fresh every evening",
    text: "At 7 pm India time the whole thing reruns on its own: new data, cleaned, forecast and published.",
  },
];

const FINDINGS = [
  {
    title: "Did Delhi's GRAP rules work?",
    text: "Once weather and the region are taken out, we can't find a first-week cut from the strictest stages.",
  },
  {
    title: "Is India's cleanest city's air clean?",
    text: "Indore is the cleanest of its neighbours, but sits right at India's yearly limit and 8× the WHO guideline.",
  },
  {
    title: "How good is the forecast?",
    text: "On months it never saw, it beat simple rules of thumb and its range held the real value 80% of the time.",
  },
];

export function About() {
  return (
    <>
      <section className="section" id="how" aria-labelledby="how-title">
        <h2 id="how-title" className="section-title">
          How it works
        </h2>
        <div className="steps">
          {STEPS.map((s) => (
            <div className="step" key={s.title}>
              <span className="step-icon">{s.icon}</span>
              <h3>{s.title}</h3>
              <p className="muted">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="find-title">
        <h2 id="find-title" className="section-title">
          What we've learned
        </h2>
        <div className="findings">
          {FINDINGS.map((f) => (
            <div className="finding" key={f.title}>
              <h3>{f.title}</h3>
              <p className="muted">{f.text}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

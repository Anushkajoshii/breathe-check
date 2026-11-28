import type { Forecast, Status } from "../data";
import { ago } from "../format";
import { LINKS } from "./Header";
import { LogoMark } from "./Icons";

export function Footer({ forecast, status }: { forecast: Forecast | null; status: Status | null }) {
  const year = new Date().getFullYear();
  return (
    <footer className="site-footer">
      {forecast && (
        <p className="freshness">
          <span className={`dot ${status && !status.ok ? "dot-warn" : "dot-ok"}`} aria-hidden="true" />
          Forecast made {ago(forecast.made_at)}
          {status && !status.ok && ". Some sources were late today, so a few numbers may be a day old"}. Updated every
          evening at 7 pm India time.
        </p>
      )}
      <div className="footer-grid">
        <div>
          <div className="footer-brand">
            <LogoMark size={24} /> <strong>Breathe Check</strong>
          </div>
          <p className="muted small">
            Air-quality forecasts from public data. PM2.5 from CPCB stations via OpenAQ, weather from Open-Meteo, fires
            from NASA FIRMS.
          </p>
        </div>
        <div>
          <p className="footer-head">Explore</p>
          <ul>
            <li>
              <a href={LINKS.report}>Findings and methods</a>
            </li>
            <li>
              <a href={LINKS.data}>Open dataset</a>
            </li>
            <li>
              <a href={LINKS.code}>Source code</a>
            </li>
          </ul>
        </div>
        <div>
          <p className="footer-head">Please note</p>
          <p className="muted small">
            These are forecasts, not medical advice. Your street can be cleaner or dirtier than the city average. If you
            have asthma or a heart condition, follow your doctor.
          </p>
        </div>
      </div>
      <p className="copyright">© {year} Anushka Joshi. All rights reserved. Code under the MIT licence.</p>
    </footer>
  );
}

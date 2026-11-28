import type { Forecast, Status } from "../data";
import { ago } from "../format";
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
            Tomorrow's cleanest hours to be outside, for 20 Indian cities. Updated every evening.
          </p>
        </div>
        <div>
          <p className="footer-head">Data sources</p>
          <p className="muted small">
            PM2.5: Central Pollution Control Board stations, via OpenAQ. Weather: Open-Meteo (CC BY 4.0). Crop fires:
            NASA FIRMS.
          </p>
        </div>
        <div>
          <p className="footer-head">Please note</p>
          <p className="muted small">
            These are forecasts, not medical advice. Your street can be cleaner or dirtier than the city average. If you
            have asthma or a heart condition, follow your doctor.
          </p>
        </div>
      </div>
      <p className="copyright">© {year} Anushka Joshi. All rights reserved.</p>
    </footer>
  );
}

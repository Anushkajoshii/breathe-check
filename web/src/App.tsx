import { useEffect, useState } from "react";
import { BestTime } from "./components/BestTime";
import { CityPicker } from "./components/CityPicker";
import { HourlyChart } from "./components/HourlyChart";
import { LastDay } from "./components/LastDay";
import { Smoke } from "./components/Smoke";
import { type Forecast, type Index, type Status, loadForecast, loadIndex, loadStatus } from "./data";
import { ago } from "./format";

const STORE_KEY = "breathe-check-city";

function savedCity(): string | null {
  const fromUrl = new URLSearchParams(window.location.search).get("city");
  if (fromUrl) return fromUrl.toLowerCase();
  try {
    return window.localStorage.getItem(STORE_KEY);
  } catch {
    return null; // private mode or blocked storage: just use the default city
  }
}

function rememberCity(slug: string) {
  try {
    window.localStorage.setItem(STORE_KEY, slug);
  } catch {
    /* not important */
  }
  const url = new URL(window.location.href);
  url.searchParams.set("city", slug);
  window.history.replaceState(null, "", url);
}

export default function App() {
  const [index, setIndex] = useState<Index | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [city, setCity] = useState<string | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctl = new AbortController();
    loadIndex(ctl.signal)
      .then((idx) => {
        setIndex(idx);
        const wanted = savedCity();
        setCity(idx.cities.some((c) => c.city === wanted) ? wanted! : idx.default_city);
      })
      .catch((e) => !ctl.signal.aborted && setError(String(e.message ?? e)));
    loadStatus(ctl.signal).then(setStatus).catch(() => undefined);
    return () => ctl.abort();
  }, []);

  useEffect(() => {
    if (!city) return;
    const ctl = new AbortController();
    setForecast(null);
    loadForecast(city, ctl.signal)
      .then(setForecast)
      .catch((e) => !ctl.signal.aborted && setError(String(e.message ?? e)));
    return () => ctl.abort();
  }, [city]);

  const choose = (slug: string) => {
    setError(null);
    setCity(slug);
    rememberCity(slug);
  };

  return (
    <div className="page">
      <header className="top">
        <div>
          <h1>Breathe Check</h1>
          <p className="muted">When is it safest to run outside tomorrow?</p>
        </div>
        {index && city && <CityPicker cities={index.cities} value={city} onChange={choose} />}
      </header>

      <main>
        {error && (
          <section className="card error" role="alert">
            <p>
              <strong>Couldn't load the forecast.</strong> {error}
            </p>
            <p className="muted small">Check your connection and reload. The forecast is made every evening at 7 pm.</p>
          </section>
        )}
        {!error && !forecast && <p className="muted loading">Loading tomorrow's forecast…</p>}
        {forecast && (
          <>
            <BestTime f={forecast} />
            <HourlyChart f={forecast} />
            {forecast.smoke ? (
              <div className="two">
                <LastDay f={forecast} />
                <Smoke f={forecast} />
              </div>
            ) : (
              <LastDay f={forecast} />
            )}
          </>
        )}
      </main>

      <footer className="foot muted small">
        {forecast && (
          <p>
            Forecast made {ago(forecast.made_at)}
            {status && !status.ok && " (some data sources were late today; numbers may be a day older than usual)"}.
            Updated every evening at 7 pm India time.
          </p>
        )}
        <p>
          PM2.5 from government (CPCB) stations via OpenAQ, weather from Open-Meteo, fires from NASA FIRMS. Not
          medical advice: if you have asthma or a heart condition, follow your doctor.
        </p>
        <p>
          <a href="https://github.com/Anushkajoshii/breathe-check">How this works</a> ·{" "}
          <a href="https://huggingface.co/datasets/Anushkajoshii/breathe-check-data">The data</a>
        </p>
      </footer>
    </div>
  );
}

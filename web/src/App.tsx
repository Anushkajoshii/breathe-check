import { useEffect, useState } from "react";
import { About } from "./components/About";
import { BestTime } from "./components/BestTime";
import { CalendarCard } from "./components/CalendarCard";
import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { HourlyChart } from "./components/HourlyChart";
import { LastDay } from "./components/LastDay";
import { Smoke } from "./components/Smoke";
import { type Forecast, type Index, type Status, loadForecast, loadIndex, loadStatus } from "./data";

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

function Skeleton() {
  return (
    <div aria-busy="true" aria-label="Loading tomorrow's forecast">
      <div className="card skeleton" style={{ height: 300 }} />
      <div className="card skeleton" style={{ height: 320 }} />
      <p className="muted small center">Loading tomorrow's forecast…</p>
    </div>
  );
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
      <Header cities={index?.cities ?? null} city={city} onCity={choose} />

      <main>
        {error && (
          <section className="card error" role="alert">
            <p>
              <strong>Couldn't load the forecast.</strong> {error}
            </p>
            <p className="muted small">Check your connection and reload. New forecasts arrive every evening at 7 pm.</p>
          </section>
        )}
        {!error && !forecast && <Skeleton />}
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
            <CalendarCard city={forecast.city} name={forecast.name} />
          </>
        )}
        <About />
      </main>

      <Footer forecast={forecast} status={status} />
    </div>
  );
}

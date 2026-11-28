import type { CityEntry } from "../data";
import { CityPicker } from "./CityPicker";
import { IconBook, IconCalendar, IconChart, LogoMark } from "./Icons";

export function Header({
  cities,
  city,
  onCity,
}: {
  cities: CityEntry[] | null;
  city: string | null;
  onCity: (slug: string) => void;
}) {
  return (
    <header className="site-header">
      <div className="brand-row">
        <a className="brand" href="/" aria-label="Breathe Check home">
          <LogoMark size={36} />
          <span>
            <span className="brand-name">Breathe Check</span>
            <span className="brand-sub">Cleaner air, better timing</span>
          </span>
        </a>
        <nav className="top-nav" aria-label="On this page">
          <a href="#forecast">
            <IconChart size={16} /> Forecast
          </a>
          <a href="#calendar">
            <IconCalendar size={16} /> Calendar
          </a>
          <a href="#how">
            <IconBook size={16} /> How it works
          </a>
        </nav>
      </div>
      <div className="intro">
        <h1>When is it safest to be outside tomorrow?</h1>
        <p className="lede">
          An hour-by-hour PM2.5 forecast for 20 Indian cities, built from government monitors and the weather.
          Pick your city and find tomorrow's cleanest two hours.
        </p>
        {cities && city && <CityPicker cities={cities} value={city} onChange={onCity} />}
      </div>
    </header>
  );
}

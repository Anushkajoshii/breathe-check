import { useState } from "react";

/** Links to subscribe to a city's run-window calendar. */
export function calendarLinks(city: string, host: string) {
  const https = `https://${host}/calendar/${city}.ics`;
  const webcal = `webcal://${host}/calendar/${city}.ics`;
  return {
    https,
    webcal,
    google: `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(webcal)}`,
  };
}

export function CalendarCard({ city, name }: { city: string; name: string }) {
  const links = calendarLinks(city, window.location.host);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(links.https);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      window.prompt("Copy this calendar link:", links.https);
    }
  };

  return (
    <section className="card" aria-labelledby="cal-title">
      <h3 id="cal-title">Get it in your calendar</h3>
      <p>
        Add once, and every evening tomorrow's best 2 hours in {name} appear in your calendar, with the PM2.5 and
        category. No app, no sign-up.
      </p>
      <div className="cal-buttons">
        <a className="button" href={links.google} target="_blank" rel="noreferrer">
          Google Calendar
        </a>
        <a className="button" href={links.webcal}>
          Apple Calendar or Outlook
        </a>
        <button type="button" className="button button-quiet" onClick={copy}>
          {copied ? "Link copied" : "Copy link"}
        </button>
      </div>
      <p className="muted small">
        Events don't mark you as busy. Google refreshes subscribed calendars every few hours, so a new day can take a
        while to appear; Apple Calendar lets you choose how often (Settings, then Refresh).
      </p>
    </section>
  );
}

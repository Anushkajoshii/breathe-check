import { useState } from "react";

/** Links to subscribe to a city's run-window calendar. */
export function calendarLinks(city: string, host: string, name = "") {
  const https = `https://${host}/calendar/${city}.ics`;
  const webcal = `webcal://${host}/calendar/${city}.ics`;
  const title = `Breathe Check: ${name || city}`;
  return {
    https,
    webcal,
    google: `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(webcal)}`,
    // Outlook on the web has its own "subscribe from web" page that takes the link directly
    outlook: `https://outlook.live.com/calendar/0/addfromweb?url=${encodeURIComponent(https)}&name=${encodeURIComponent(title)}`,
  };
}

export function CalendarCard({ city, name }: { city: string; name: string }) {
  const links = calendarLinks(city, window.location.host, name);
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
        <a className="button" href={links.outlook} target="_blank" rel="noreferrer">
          Outlook
        </a>
        <a className="button" href={links.webcal}>
          Apple Calendar
        </a>
        <button type="button" className="button button-quiet" onClick={copy}>
          {copied ? "Link copied" : "Copy link"}
        </button>
      </div>
      <p className="muted small">
        <strong>Apple Calendar</strong> opens the Calendar app on iPhone and on Mac in Safari. If nothing happens (some
        browsers, like Chrome, don't pass these links on), copy the link and in Calendar choose File, then New Calendar
        Subscription. On iPhone: Settings, Calendar, Accounts, Add Account, Other, Add Subscribed Calendar.
      </p>
      <p className="muted small">
        Events don't mark you as busy. Google and Outlook refresh subscribed calendars every few hours, so a new day can
        take a while to appear; Apple Calendar lets you choose how often.
      </p>
    </section>
  );
}

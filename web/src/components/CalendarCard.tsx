import { useState } from "react";
import { IconCalendar, IconCheck, IconCopy } from "./Icons";

/** Links to subscribe to a city's run-window calendar. */
export function calendarLinks(city: string, host: string, name = "") {
  const https = `https://${host}/calendar/${city}.ics`;
  const webcal = `webcal://${host}/calendar/${city}.ics`;
  const title = `Breathe Check: ${name || city}`;
  return {
    https,
    webcal,
    google: `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(webcal)}`,
    outlook: `https://outlook.live.com/calendar/0/addfromweb?url=${encodeURIComponent(https)}&name=${encodeURIComponent(title)}`,
  };
}

/**
 * iPhone and iPad open webcal:// links in the Calendar app reliably. On a Mac,
 * whichever app registered for webcal:// gets the link (often Chrome, which can't
 * use it), so there we show the two-step way instead.
 */
export function deviceKind(ua: string, maxTouchPoints: number): "ios" | "mac" | "other" {
  if (/iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && maxTouchPoints > 1)) return "ios";
  if (/Macintosh/.test(ua)) return "mac";
  return "other";
}

export function CalendarCard({ city, name }: { city: string; name: string }) {
  const links = calendarLinks(city, window.location.host, name);
  const device = deviceKind(navigator.userAgent, navigator.maxTouchPoints ?? 0);
  const [copied, setCopied] = useState(false);
  const [appleHelp, setAppleHelp] = useState(false);

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
    <section className="card calendar" aria-labelledby="cal-title">
      <div className="card-head">
        <span className="card-icon">
          <IconCalendar />
        </span>
        <h3 id="cal-title">Get it in your calendar</h3>
      </div>
      <p className="lead-line">
        Subscribe once. Every evening, tomorrow's best two hours in {name} land in your calendar, with the PM2.5 and
        what it means. No app, no sign-up.
      </p>
      <div className="cal-buttons">
        <a className="button" href={links.google} target="_blank" rel="noreferrer">
          <GoogleMark /> Google Calendar
        </a>
        <a className="button" href={links.outlook} target="_blank" rel="noreferrer">
          <OutlookMark /> Outlook
        </a>
        {device === "ios" ? (
          <a className="button" href={links.webcal}>
            <AppleMark /> Apple Calendar
          </a>
        ) : (
          <button
            type="button"
            className="button"
            aria-expanded={appleHelp}
            aria-controls="apple-help"
            onClick={() => {
              setAppleHelp((v) => !v);
              copy();
            }}
          >
            <AppleMark /> Apple Calendar
          </button>
        )}
        <button type="button" className="button button-quiet" onClick={copy}>
          {copied ? <IconCheck size={16} /> : <IconCopy size={16} />} {copied ? "Link copied" : "Copy link"}
        </button>
      </div>
      {appleHelp && (
        <div id="apple-help" className="apple-help" role="region" aria-label="Add to Apple Calendar on a Mac">
          <p>
            <strong>On a Mac, two quick steps.</strong> We've copied the link for you.
          </p>
          <ol>
            <li>
              Open <strong>Calendar</strong>, then choose <strong>File → New Calendar Subscription…</strong>
            </li>
            <li>
              Paste the link, press <strong>Subscribe</strong>, and set Auto-refresh to <strong>Every hour</strong>.
            </li>
          </ol>
          <code className="cal-link">{links.https}</code>
        </div>
      )}
      <p className="muted small">
        Events never mark you as busy. Google and Outlook check for updates every few hours, so a new day can take a
        while to appear. On iPhone, Apple Calendar opens directly.
      </p>
    </section>
  );
}

const GoogleMark = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
    <rect x="3" y="3" width="18" height="18" rx="3" fill="#fff" />
    <path d="M3 8h18" stroke="#4285f4" strokeWidth="3" />
    <text x="12" y="19" textAnchor="middle" fontSize="9" fontWeight="700" fill="#4285f4" fontFamily="Arial">
      31
    </text>
  </svg>
);
const OutlookMark = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
    <rect x="3" y="4" width="18" height="16" rx="3" fill="#fff" />
    <circle cx="10" cy="12" r="4" fill="none" stroke="#0a64d6" strokeWidth="2.5" />
    <path d="M15 9h4v6h-4" fill="none" stroke="#0a64d6" strokeWidth="2" />
  </svg>
);
const AppleMark = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
    <path d="M16.4 12.6c0-2.5 2-3.6 2.1-3.7-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.7.9s-2-.9-3.2-.8c-1.7 0-3.2 1-4 2.4-1.7 3-.4 7.4 1.2 9.8.8 1.2 1.8 2.5 3 2.4 1.2 0 1.7-.8 3.1-.8s1.9.8 3.2.8 2.1-1.2 2.9-2.4c.9-1.4 1.3-2.7 1.3-2.8 0 0-2.4-.9-2.3-3.8zM14 5.1c.6-.8 1.1-1.9 1-3-1 0-2.1.6-2.8 1.4-.6.7-1.2 1.8-1 2.9 1.1.1 2.2-.5 2.8-1.3z" />
  </svg>
);

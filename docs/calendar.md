# The run-window calendar

Add one link to your calendar, once. Every evening, tomorrow's best 2 hours to be outside in your city appear as an event, with the PM2.5, the India AQI category and the advice. There's no app and no sign-up.

## Add it

Open the app at **https://breathecheck-aj.vercel.app**, choose your city, and use **Get it in your calendar**. Or add the link yourself:

```
https://breathecheck-aj.vercel.app/calendar/<city>.ics
```

For example, `indore.ics`, `delhi.ics` or `bengaluru.ics`. All 20 cities: ahmedabad, bengaluru, bhopal, chandigarh, chennai, delhi, faridabad, ghaziabad, gurugram, hyderabad, indore, jaipur, kanpur, kolkata, lucknow, mumbai, nagpur, noida, patna, pune.

- **Google Calendar:** Other calendars → **+** → **From URL** → paste the link.
- **Apple Calendar:** on iPhone and iPad, the app's **Apple Calendar** button opens the Calendar app straight away. On a Mac, the button copies the link and shows two steps instead: Calendar → **File → New Calendar Subscription…** → paste → **Subscribe**, with Auto-refresh set to every hour. (A Mac hands `webcal://` links to whichever app registered for them, often Chrome, which can't use them, so the app doesn't rely on them there.) On iPhone without the app: Settings → Calendar → Accounts → Add Account → Other → **Add Subscribed Calendar**.
- **Outlook:** the app's **Outlook** button opens Outlook's "subscribe from web" page with the link filled in. Or: Add calendar → **Subscribe from web** → paste the link.

## What an event looks like

> **Indore: best time to run or go out** (noon to 2 pm)
> Noon to 2 pm on Sunday 29 November is the cleanest window in Indore.
> Air quality: Good, PM2.5 about 28 µg/m³. Great day to be outside.
> Two hours outside at this level is like 0.1 of a cigarette (Berkeley Earth's rough rule of thumb, not a medical measure).
> Worst hour: around 11 pm, about 52 µg/m³.
> Hour by hour: https://breathecheck-aj.vercel.app/?city=indore

- **Events don't mark you as busy.**
- **Delhi-NCR cities** add a line when crop-fire smoke is likely.

## How it works

- **The daily job** (7 pm India time) makes tomorrow's forecast, then `breathe_check.calendar_feed` adds one event per city to that city's feed. It keeps the last 14 days, so your calendar shows a short history.
- **The files** go to the Hugging Face dataset at `public/calendar/<city>.ics`. Each feed's event history sits next to it as `<city>.json`, which the next day's job reads.
- **The app's site** serves `/calendar/<city>.ics` by passing the file through from Hugging Face (a rewrite in `web/vercel.json`). It's labelled `text/calendar`, so calendar apps recognise it.
- **Event times are in UTC,** which every calendar app converts to your own time zone.
- **A later forecast for the same day replaces the earlier event** (same event ID), so you never get duplicates.

## Limits

- **Google Calendar refreshes subscriptions only every few hours,** sometimes up to a day. Apple Calendar lets you choose. If tomorrow's event hasn't appeared yet, the app always has the latest.
- **The window is a forecast,** with the same limits as the app: see [the run-window report](../reports/05-run-window.md).

## The app's address changed

The app moved from `breathe-check-flax.vercel.app` to **breathecheck-aj.vercel.app** in November 2026. Feeds and links now use the new address, and events already in your calendar pick up the new link at the next refresh. If you subscribed with the old address, it keeps working only while the old address still points at the app. Re-subscribing with the new link is the safe choice.

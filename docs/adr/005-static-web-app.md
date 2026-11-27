# ADR-005: A small static web app that reads the forecasts straight from Hugging Face

**Status:** Accepted, November 2026

## Context

People need one page that answers "when should I go out tomorrow?" in a few seconds on a phone. The forecasts are already made every evening as small JSON files on Hugging Face (ADR-004).

## Decision

- **React + Vite + TypeScript, built to plain static files** and hosted on Vercel's free plan. There's no server and no database.
- **The page fetches** `public/forecast/index.json`, `public/forecast/<city>.json` and `public/status.json` from the Hugging Face dataset. Hugging Face allows browsers to read these files from other sites (CORS), and every evening's update appears without redeploying the app.
- **The chart is hand-made in SVG,** not a charting library. That keeps the app small (about 73 KB of code after compression) and gives full control over accessibility.
- **Every category shows as an icon and words,** not colour alone. The chart has a hover tooltip, keyboard focus for each hour, and a table view with the same numbers.
- **Light and dark themes,** each with its own colour set, chosen by the phone or computer setting.
- **The chosen city is remembered** in the browser and kept in the link (`?city=delhi`), so a link can be shared.

## Consequences

- **The first load waits on Hugging Face,** which can take a couple of seconds. A loading line shows meanwhile.
- **If Hugging Face is down,** the page says it couldn't load the forecast. It never shows made-up numbers.
- **Vercel needs one-time setup by the account owner:** import the GitHub repo and set the root folder to `web`. After that, every push to `main` redeploys automatically.

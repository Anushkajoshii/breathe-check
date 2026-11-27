# Putting the web app online (Vercel)

The app in `web/` is a plain static site. Vercel's free plan hosts it and redeploys every time `main` changes.

## One-time setup (about 3 minutes)

1. Sign in at [vercel.com](https://vercel.com) with your GitHub account.
2. Click **Add New… → Project** and pick **Anushkajoshii/breathe-check**. Allow Vercel to see that repo if it asks.
3. Set **Root Directory** to `web`. Vercel reads `web/vercel.json` for the rest (Vite, `npm ci`, `npm run build`, output folder `dist`).
4. Leave the environment variables empty. The app reads the public dataset by default.
5. Click **Deploy**. In a minute you get a link like `breathe-check.vercel.app`.

## After that

- **Every push to `main`** redeploys the site. Pull requests get their own preview link.
- **The forecasts update by themselves** every evening. The app reads them from Hugging Face, so no redeploy is needed for new data.
- **To change the site's name,** go to Vercel → the project → **Settings → Domains**.

## Run it on your own computer

```bash
cd web
npm install
npm run dev
```

Then open http://localhost:5173. Add `?city=delhi` to the address to open a city directly.

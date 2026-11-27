# Reference dates

Small hand-made tables the analysis needs. They are kept in git (not on Hugging Face) so every change is reviewed. Anyone is welcome to reuse them.

## `grap_orders.csv`: every revised-GRAP stage order, October 2022 onwards

One row per stage per order. If an order changed two stages, it gets two rows.

| Column | Meaning |
|---|---|
| `order_date` | Date the CAQM order was issued |
| `action` | `invoke` (switch on) or `revoke` (switch off) |
| `stage` | 1 to 4 (Stage I to Stage IV) |
| `note` | Anything unusual about the order |
| `source_url` | Where the date came from |
| `checked_against` | How well the date is backed up (see below) |
| `needs_review` | `yes` if the sources disagree or the row is unclear |

How well each date is backed up, from strongest to weakest:
- `caqm_pdf_link`: the source links to the order PDF on caqm.nic.in
- `pib`: a Government of India press release (PIB)
- `public_broadcaster`: All India Radio News (newsonair.gov.in)
- `tracker`: the [grapinfo.com order list](https://grapinfo.com/grap-orders.php), which lists CAQM orders by title
- `news`: a national news report from the same day
- `news_only`: the tracker picked it up from news, with no order found

Stages stack: Stage III on means Stages I and II are on too. Revoking Stage III drops the city back to Stage II. `breathe_check.grap.daily_stage()` turns these rows into one number per day, and `check_orders()` makes sure no stage is revoked while it's off.

**Rows left out on purpose**
- 2022-11-09: an order about painting and polishing work. It didn't switch a stage on or off.
- 2024-11-28: a clarification about construction work, and its withdrawal.
- 2025-11-21: an update to what each stage includes, with no stage change.
- 2026-11-17 "revoke Stage I": the tracker lists it, but the government press release from that day says Stages I and II stay on.

## `grap_original_seasons.csv`: the original GRAP, 2017 to 2022

The first GRAP was notified in January 2017 and applied every winter from 15 October to 15 March. Its measures switched on automatically by AQI level, and no day-by-day record of stages was published. So for these winters we only use the season window, and compare Delhi-NCR with cities outside it over the same window.

## `diwali.csv`: Diwali (Lakshmi Puja) date each year

Used to measure the firecracker spike separately from GRAP. Diwali often falls in the same weeks as GRAP stage changes, so ignoring it would mix the two.

# Draft: "I tried to check whether Delhi's smog rules work. The weather kept getting in the way."

*A draft for Medium. Edit freely before publishing. Numbers are from the project as of November 2026; check the [report site](https://anushkajoshii.github.io/breathe-check/) for the latest.*

---

Every winter, the same headline comes around: Delhi's air hits "Severe", the authorities switch on a stricter stage of GRAP (the Graded Response Action Plan), construction stops, older diesel cars come off the road, and a few days later the air improves. It's easy to read that as cause and effect.

I wanted to know if it really was. And while I was at it, two smaller questions I'd always wondered about: Indore keeps being named India's cleanest city, but is its *air* clean? And if I want to run outside tomorrow, when is the least bad time?

I built a small project, Breathe Check, to answer all three with public data only. Here's what I learned, including the parts that didn't go the way I expected.

## The data was the first surprise

I used hourly PM2.5 readings from 225 government (CPCB) monitoring stations near 20 cities, through OpenAQ, plus weather from Open-Meteo and NASA's satellite fire detections for Punjab and Haryana.

Two things showed up immediately.

**There's a three-year hole.** OpenAQ has almost no CPCB data from November 2022 to February 2025. Three whole winters are missing. I could still work with four winters before and two after, but it shaped everything that followed.

**Broken sensors make cities look cleaner.** Some stations, when they go offline, keep reporting zero. Averaged in, those zeros dragged Indore's 2026 average from 41 µg/m³ down to 37. Once I wrote proper cleaning rules (impossible values, stuck sensors, days with too few hours), about a fifth of daily readings were set aside. That sounds like a lot, but it's mostly days where a station only reported for a few hours.

## The weather is a bigger deal than I thought

Before you can judge any rule, you have to deal with the weather. On a calm, cold, damp winter night, a lid of warm air sits over the city and traps everything underneath. When the wind picks up or the sun warms the ground in the afternoon, the air mixes and clears.

How big is that effect? On Delhi's winter days with the lowest "mixing height" (how high the air can rise), PM2.5 averaged 231 µg/m³. On the days with the highest, 140. Same city, same season, 40% less pollution, from weather alone.

So I trained a model for each city that predicts PM2.5 from the weather and the time of year, and nothing else. It never sees GRAP stages, fires or festivals. Tested on whole winters it had never seen, Delhi's model got 80% of the day-to-day ups and downs right. Whatever it *can't* explain is what's left for things like rules, fires and Diwali.

## Did GRAP work?

Here's the trap. GRAP stages are switched on *because* the air is unusually bad. Bad spells end on their own. So if you just compare the week before a stage with the week after, the stage will almost always look like it worked, or, in the other direction, like it made things worse.

That's exactly what the raw numbers did. After Delhi-NCR's strictest stages (III and IV) were switched on, PM2.5 went **up** by 37% the following week. After they were switched off, it went **down** by 31%. Neither tells you anything about the rules. Orders now go out early, on forecasts of a bad spell that hasn't peaked yet, and they're lifted once it's clearing.

To get closer to the truth, I did two things:

1. **Took the weather out**, using the model above.
2. **Compared Delhi-NCR with cities that share its winters but not its rules:** Lucknow, Kanpur, Patna and Chandigarh, on the same Indo-Gangetic plain. If a bad spell hits the whole region, it cancels out.

What was left: **+8%**, with a 90% range from −5% to +23%. Then I ran the same calculation on thousands of random winter dates when no stage changed, and got results that big 38% of the time.

So my honest answer is: **in the first week, I can't find a cut.** That's not the same as "GRAP doesn't work". There were only four strict-stage events in the data I had (thanks to that three-year hole), the method only looks one week either side, and some measures may work slowly over a whole season. But a large, quick drop, the kind the headlines imply, is hard to believe.

What surprised me most was a chart of the days *before* each order. Delhi-NCR was already pulling ahead of its neighbours, getting worse faster, in the days leading up to the order. You can literally see the "switched on because it was bad" effect in the data.

## India's cleanest city

Indore has topped the Swachh Survekshan cleanliness survey year after year. That survey scores waste collection and how clean the streets look. It doesn't measure air.

For July 2025 to June 2026, the first full year with Indore's new network of five or six stations, Indore averaged **41 µg/m³** of PM2.5. India's yearly limit is 40. The WHO's guideline is 5.

So Indore is:

- the **cleanest** of its neighbours (Ahmedabad 42, Nagpur 45, Bhopal 49, Jaipur 53),
- **right at** India's own limit,
- about **8 times** the WHO guideline, roughly like smoking 1.8 cigarettes a day (Berkeley Earth's rule of thumb).

Then I asked: is Indore cleaner because of something it does, or because of its weather? I trained one shared weather model for all 20 cities, so every city is judged by the same rule. Indore came out almost exactly as clean as its weather predicts (3% below). Its lead over Bhopal and Jaipur looks mostly like weather and geography. Clean streets haven't bought cleaner air beyond what nature already gives.

## When should you run?

This is the part people actually use. Every evening at 7 pm, an automated job pulls in the day's data and forecasts PM2.5 for every hour of tomorrow, with a range, for 20 cities. It picks the best two hours to be outside.

The honest scorecard, from months the model never saw:

- It misses by about **12 µg/m³** an hour on average, better than "tomorrow will be like today" (14) or "the usual for this hour" (18).
- Its range holds the real value **80%** of the time, which is what it promises. I had to widen it to get there. It started at 73%.
- Its "best window" was among the day's cleanest third on **63%** of days. Always going at 2 pm managed 48%.

And the honest caveat: **in winter, just going at 2 pm works as well as the forecast.** The afternoon sun reliably lifts the lid off the city. The forecast earns its keep the rest of the year, and by telling you *how* clean the window will be.

You can see it at [breathe-check-flax.vercel.app](https://breathe-check-flax.vercel.app), or add your city's calendar feed and tomorrow's window shows up in Google Calendar, Outlook or Apple Calendar every evening.

## Things that broke, and what I learned

- **A satellite stopped.** NASA's near-real-time fire feed from the Suomi NPP satellite stopped on 2 November 2026. My "latest fire data" was suddenly 25 days old. The fix was to switch to NOAA-20, which carries the same instrument. On the two days both had data, they counted 235 vs 268 and 245 vs 258 fires: close enough for a smoke check.
- **IPv6.** The daily job worked on my laptop but couldn't reach NASA from GitHub's servers. NASA's server prefers IPv6, and GitHub's runners don't have it. One line to force IPv4 fixed it.
- **A tiny date bug** was silently dropping every reading from "today". Running the whole pipeline from an empty machine caught it.

Most of the work wasn't the model. It was data cleaning, honest testing, and making the boring parts reliable enough to run every evening without me.

## Try it, check it

Everything is free and public:

- **App:** [breathe-check-flax.vercel.app](https://breathe-check-flax.vercel.app)
- **Full write-up:** [anushkajoshii.github.io/breathe-check](https://anushkajoshii.github.io/breathe-check/)
- **Code:** [github.com/Anushkajoshii/breathe-check](https://github.com/Anushkajoshii/breathe-check)
- **Data:** [huggingface.co/datasets/Anushkajoshii/breathe-check-data](https://huggingface.co/datasets/Anushkajoshii/breathe-check-data)

If you spot something I got wrong, I'd genuinely like to know.

*Not medical advice. If you have asthma or a heart condition, follow your doctor.*

import { useId, useMemo, useState } from "react";
import type { Forecast, Hour } from "../data";
import { hourLabel, INDIA_DAILY } from "../format";
import { IconChart } from "./Icons";
import { LevelBadge } from "./LevelBadge";

const W = 640;
const PAD = { top: 16, right: 16, bottom: 30, left: 40 };

/** Taller on phones, where the chart is drawn narrow, so the hourly shape stays readable. */
function chartHeight(): number {
  return typeof window !== "undefined" && window.matchMedia?.("(max-width: 520px)").matches ? 420 : 260;
}

/**
 * Tomorrow hour by hour: the middle forecast as a line, the low-high range as a band,
 * the best window shaded. Hover or tab through the hours for exact numbers; a table
 * with the same numbers sits underneath for screen readers and anyone who prefers it.
 */
export function HourlyChart({ f }: { f: Forecast }) {
  const hours = useMemo(() => [...f.hours].sort((a, b) => a.hour - b.hour), [f.hours]);
  const [active, setActive] = useState<Hour | null>(null);
  const titleId = useId();
  const H = chartHeight();

  const yMax = Math.max(...hours.map((h) => h.high), INDIA_DAILY) * 1.1;
  const x = (h: number) => PAD.left + (h / 23) * (W - PAD.left - PAD.right);
  const y = (v: number) => PAD.top + (1 - v / yMax) * (H - PAD.top - PAD.bottom);

  const line = hours.map((h, i) => `${i ? "L" : "M"}${x(h.hour)},${y(h.mid)}`).join(" ");
  const band =
    hours.map((h, i) => `${i ? "L" : "M"}${x(h.hour)},${y(h.high)}`).join(" ") +
    " " +
    [...hours].reverse().map((h) => `L${x(h.hour)},${y(h.low)}`).join(" ") +
    " Z";
  const ticks = niceTicks(yMax);
  const best = f.best_window;

  return (
    <section className="card" aria-labelledby={titleId}>
      <div className="card-head">
        <span className="card-icon">
          <IconChart />
        </span>
        <h3 id={titleId}>Tomorrow, hour by hour</h3>
      </div>
      <ul className="legend" aria-label="Chart key">
        <li>
          <span className="key key-line" /> Forecast
        </li>
        <li>
          <span className="key key-band" /> Likely range (8 in 10)
        </li>
        <li>
          <span className="key key-best" /> Best 2 hours
        </li>
      </ul>
      <div className="chart-wrap">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="chart"
          role="img"
          aria-label={`PM2.5 forecast for ${f.name}, hour by hour. Details in the table below.`}
          onMouseLeave={() => setActive(null)}
        >
          {ticks.map((t) => (
            <g key={t}>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} className="grid" />
              {t > 0 && (
                <text x={PAD.left - 6} y={y(t)} className="axis" textAnchor="end" dominantBaseline="middle">
                  {t}
                </text>
              )}
            </g>
          ))}
          {best && (
            <rect
              x={x(best.start)}
              width={x(Math.min(best.end, 23)) - x(best.start)}
              y={PAD.top}
              height={H - PAD.top - PAD.bottom}
              className="best-zone"
            />
          )}
          {best && (
            <text x={(x(best.start) + x(Math.min(best.end, 23))) / 2} y={PAD.top + 14} className="best-label" textAnchor="middle">
              Best
            </text>
          )}
          <line x1={PAD.left} x2={W - PAD.right} y1={y(INDIA_DAILY)} y2={y(INDIA_DAILY)} className="limit" />
          <text x={PAD.left + 4} y={y(INDIA_DAILY) - 5} className="axis" textAnchor="start">
            India daily limit (60)
          </text>
          <path d={band} className="band" />
          <path d={line} className="line" />
          {[0, 6, 12, 18, 23].map((h) => (
            <text key={h} x={x(h)} y={H - 8} className="axis" textAnchor="middle">
              {hourLabel(h)}
            </text>
          ))}
          {active && (
            <g>
              <line x1={x(active.hour)} x2={x(active.hour)} y1={PAD.top} y2={H - PAD.bottom} className="crosshair" />
              <circle cx={x(active.hour)} cy={y(active.mid)} r={5} className="dot" />
            </g>
          )}
          {hours.map((h) => (
            <rect
              key={h.hour}
              x={x(h.hour) - (W - PAD.left - PAD.right) / 46}
              width={(W - PAD.left - PAD.right) / 23}
              y={PAD.top}
              height={H - PAD.top - PAD.bottom}
              fill="transparent"
              tabIndex={0}
              aria-label={`${hourLabel(h.hour)}: about ${Math.round(h.mid)}, between ${Math.round(h.low)} and ${Math.round(h.high)} micrograms`}
              onMouseEnter={() => setActive(h)}
              onFocus={() => setActive(h)}
              onBlur={() => setActive(null)}
            />
          ))}
        </svg>
        {active && (
          <div
            className="tooltip"
            style={{ left: `${(x(active.hour) / W) * 100}%` }}
            role="status"
          >
            <strong>{hourLabel(active.hour)}</strong>
            <span>
              about {Math.round(active.mid)} µg/m³ <LevelBadge category={active.category} />
            </span>
            <span className="muted small">
              likely {Math.round(active.low)} to {Math.round(active.high)}
            </span>
          </div>
        )}
      </div>
      <details className="table-view">
        <summary>Show as a table</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Hour</th>
              <th scope="col">Low</th>
              <th scope="col">Middle</th>
              <th scope="col">High</th>
              <th scope="col">Category</th>
            </tr>
          </thead>
          <tbody>
            {hours.map((h) => (
              <tr key={h.hour}>
                <th scope="row">{hourLabel(h.hour)}</th>
                <td>{Math.round(h.low)}</td>
                <td>{Math.round(h.mid)}</td>
                <td>{Math.round(h.high)}</td>
                <td>{h.category}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}

export function niceTicks(max: number): number[] {
  const step = max <= 60 ? 10 : max <= 150 ? 25 : max <= 300 ? 50 : 100;
  const out: number[] = [];
  for (let v = 0; v <= max; v += step) out.push(v);
  return out;
}

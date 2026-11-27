import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";
import type { Forecast, Index, Status } from "./data";

const hours = Array.from({ length: 24 }, (_, h) => ({
  hour: h,
  low: 20,
  mid: h === 12 || h === 13 ? 25 : 45,
  high: 70,
  category: "Satisfactory" as const,
}));

const indore: Forecast = {
  city: "indore",
  name: "Indore",
  state: "Madhya Pradesh",
  for_date: "2026-11-29",
  made_at: "2026-11-28T19:12",
  hours,
  best_window: { start: 12, end: 14, pm25: 25, category: "Good", advice: "Great day to be outside." },
  worst_hour: 22,
  today: {
    pm25: 35.3,
    cigarettes: 1.6,
    aqi_category: "Satisfactory",
    advice: "Fine for most people.",
    label: "Last 24 hours",
    until: "2026-11-28T18:00",
  },
  based_on_air_up_to: "2026-11-28",
  smoke: null,
};

const delhi: Forecast = {
  ...indore,
  city: "delhi",
  name: "Delhi",
  smoke: { level: "Likely", why: "2,100 fires seen on 27 Nov; wind from the north-west for 70% of the forecast hours." },
};

const index: Index = {
  made_at: "2026-11-28T19:12",
  for_date: "2026-11-29",
  default_city: "indore",
  cities: [
    { city: "indore", name: "Indore", state: "Madhya Pradesh", best_window: indore.best_window },
    { city: "delhi", name: "Delhi", state: "Delhi", best_window: delhi.best_window },
  ],
};

const status: Status = { started_at: "", finished_at: "", ok: true, steps: {}, data_up_to: {} };

function mockFetch(files: Record<string, unknown>) {
  globalThis.fetch = vi.fn(async (url: string | URL | Request) => {
    const path = String(url).split("/public/")[1].split("?")[0];
    const body = files[path];
    return body
      ? new Response(JSON.stringify(body), { status: 200 })
      : new Response("missing", { status: 404 });
  }) as typeof fetch;
}

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  window.localStorage.clear();
});

test("shows Indore's best time by default", async () => {
  mockFetch({ "forecast/index.json": index, "forecast/indore.json": indore, "status.json": status });
  render(<App />);
  expect(await screen.findByText("noon to 2 pm")).toBeInTheDocument();
  expect(screen.getByText(/about 1.6 cigarettes/)).toBeInTheDocument();
  expect(screen.queryByText(/Crop-fire smoke/)).not.toBeInTheDocument();
});

test("a city in the link is used, and the smoke card shows for Delhi", async () => {
  window.history.replaceState(null, "", "/?city=delhi");
  mockFetch({ "forecast/index.json": index, "forecast/delhi.json": delhi, "status.json": status });
  render(<App />);
  expect(await screen.findByText("Likely")).toBeInTheDocument();
  expect(screen.getByRole("combobox")).toHaveValue("delhi");
});

test("a clear message when the forecast can't load", async () => {
  mockFetch({});
  render(<App />);
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Couldn't load the forecast"));
});

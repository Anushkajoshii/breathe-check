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
    const path = String(url).replace(/^.*\/data\//, "").split("?")[0];
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
  // shown in the summary tile and in the last-24-hours card
  expect(screen.getAllByText(/about 1.6 cigarettes/).length).toBeGreaterThan(0);
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

test("calendar links point at the city's feed on this site", async () => {
  const { calendarLinks } = await import("./components/CalendarCard");
  const links = calendarLinks("indore", "breathecheck-aj.vercel.app", "Indore");
  expect(links.https).toBe("https://breathecheck-aj.vercel.app/calendar/indore.ics");
  expect(links.webcal).toBe("webcal://breathecheck-aj.vercel.app/calendar/indore.ics");
  expect(links.google).toContain(encodeURIComponent("webcal://breathecheck-aj.vercel.app/calendar/indore.ics"));
  expect(links.outlook).toBe(
    "https://outlook.live.com/calendar/0/addfromweb?url=" +
      encodeURIComponent("https://breathecheck-aj.vercel.app/calendar/indore.ics") +
      "&name=" +
      encodeURIComponent("Breathe Check: Indore"),
  );
});

test("the calendar card shows under the forecast", async () => {
  mockFetch({ "forecast/index.json": index, "forecast/indore.json": indore, "status.json": status });
  render(<App />);
  expect(await screen.findByText("Get it in your calendar")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Google Calendar" })).toHaveAttribute(
    "href",
    expect.stringContaining("calendar.google.com"),
  );
});

test("Apple Calendar on a Mac shows the two-step help instead of a webcal link", async () => {
  const { deviceKind } = await import("./components/CalendarCard");
  const mac = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15";
  const iphone = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1";
  expect(deviceKind(iphone, 5)).toBe("ios");
  expect(deviceKind(mac, 5)).toBe("ios"); // an iPad asking for the desktop site
  expect(deviceKind(mac, 0)).toBe("mac");
  expect(deviceKind("Mozilla/5.0 (Windows NT 10.0)", 0)).toBe("other");

  mockFetch({ "forecast/index.json": index, "forecast/indore.json": indore, "status.json": status });
  window.prompt = vi.fn(); // the test browser has no clipboard, so copying falls back to this
  render(<App />);
  const apple = await screen.findByRole("button", { name: /Apple Calendar/ });
  apple.click();
  expect(await screen.findByText(/New Calendar Subscription/)).toBeInTheDocument();
});

test("the footer carries the copyright", async () => {
  mockFetch({ "forecast/index.json": index, "forecast/indore.json": indore, "status.json": status });
  render(<App />);
  expect(await screen.findByText(/© \d{4} Anushka Joshi/)).toBeInTheDocument();
});

test("the app links nowhere outside itself except calendar services", async () => {
  mockFetch({ "forecast/index.json": index, "forecast/indore.json": indore, "status.json": status });
  render(<App />);
  await screen.findByText("noon to 2 pm");
  const external = [...document.querySelectorAll("a[href^='http']")]
    .map((a) => a.getAttribute("href") ?? "")
    .filter((h) => !/calendar\.google\.com|outlook\.live\.com/.test(h));
  expect(external).toEqual([]);
  expect(document.body.innerHTML).not.toMatch(/github|huggingface/i);
});

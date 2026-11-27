// Where the app gets its numbers: small JSON files the daily job uploads to the
// public Hugging Face dataset every evening at 7 pm India time.

export const DATA_BASE =
  import.meta.env.VITE_DATA_BASE ??
  "https://huggingface.co/datasets/Anushkajoshii/breathe-check-data/resolve/main/public";

export type Category = "Good" | "Satisfactory" | "Moderate" | "Poor" | "Very Poor" | "Severe";

export interface Hour {
  hour: number;
  low: number;
  mid: number;
  high: number;
  category: Category;
}

export interface Forecast {
  city: string;
  name: string;
  state: string;
  for_date: string;
  made_at: string;
  hours: Hour[];
  best_window: { start: number; end: number; pm25: number; category: Category; advice: string } | null;
  worst_hour: number;
  today: {
    pm25: number;
    cigarettes: number;
    aqi_category: Category;
    advice: string;
    label: string;
    until: string;
  } | null;
  based_on_air_up_to: string | null;
  smoke: { level: string; why: string } | null;
}

export interface CityEntry {
  city: string;
  name: string;
  state: string;
  best_window: Forecast["best_window"];
}

export interface Index {
  made_at: string;
  for_date: string;
  default_city: string;
  cities: CityEntry[];
}

export interface Status {
  started_at: string;
  finished_at: string;
  ok: boolean;
  steps: Record<string, string>;
  data_up_to: Record<string, string>;
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  // A cache-busting query keeps phones from showing yesterday's file.
  const day = new Date().toISOString().slice(0, 13);
  const res = await fetch(`${DATA_BASE}/${path}?v=${day}`, { signal });
  if (!res.ok) throw new Error(`Could not load ${path} (${res.status})`);
  return (await res.json()) as T;
}

export const loadIndex = (signal?: AbortSignal) => getJson<Index>("forecast/index.json", signal);
export const loadForecast = (city: string, signal?: AbortSignal) =>
  getJson<Forecast>(`forecast/${city}.json`, signal);
export const loadStatus = (signal?: AbortSignal) => getJson<Status>("status.json", signal);

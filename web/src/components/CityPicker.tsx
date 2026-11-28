import type { CityEntry } from "../data";

export function CityPicker({
  cities,
  value,
  onChange,
}: {
  cities: CityEntry[];
  value: string;
  onChange: (slug: string) => void;
}) {
  const sorted = [...cities].sort((a, b) => a.name.localeCompare(b.name));
  return (
    <label className="picker">
      <span className="picker-label">Your city</span>
      <span className="select-wrap">
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          {sorted.map((c) => (
            <option key={c.city} value={c.city}>
              {c.name}, {c.state}
            </option>
          ))}
        </select>
      </span>
    </label>
  );
}

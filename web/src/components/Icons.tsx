// Small line icons, drawn in the text colour. Decorative: always paired with words.
type P = { size?: number };
const base = (size = 18) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
});

export const IconWind = ({ size }: P) => (
  <svg {...base(size)}><path d="M3 8h11a3 3 0 1 0-3-3" /><path d="M3 12h16a3 3 0 1 1-3 3" /><path d="M3 16h7" /></svg>
);
export const IconClock = ({ size }: P) => (
  <svg {...base(size)}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
);
export const IconTrendUp = ({ size }: P) => (
  <svg {...base(size)}><path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" /></svg>
);
export const IconLungs = ({ size }: P) => (
  <svg {...base(size)}><path d="M12 4v8" /><path d="M12 12c-2 0-3-2-5-2-2.5 0-4 4-4 7 0 2 1 3 3 3 3 0 6-2 6-5" /><path d="M12 12c2 0 3-2 5-2 2.5 0 4 4 4 7 0 2-1 3-3 3-3 0-6-2-6-5" /></svg>
);
export const IconFlame = ({ size }: P) => (
  <svg {...base(size)}><path d="M12 3c1 4 5 5 5 10a5 5 0 0 1-10 0c0-3 2-4 2-7 1 1 2 2 3 4 0-3 0-5 0-7z" /></svg>
);
export const IconCalendar = ({ size }: P) => (
  <svg {...base(size)}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>
);
export const IconChart = ({ size }: P) => (
  <svg {...base(size)}><path d="M4 19h16" /><path d="M4 15l4-5 4 3 5-7 3 4" /></svg>
);
export const IconBook = ({ size }: P) => (
  <svg {...base(size)}><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z" /><path d="M4 19V5" /></svg>
);
export const IconDatabase = ({ size }: P) => (
  <svg {...base(size)}><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5" /><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6" /></svg>
);
export const IconCode = ({ size }: P) => (
  <svg {...base(size)}><path d="M8 7l-5 5 5 5M16 7l5 5-5 5" /></svg>
);
export const IconCopy = ({ size }: P) => (
  <svg {...base(size)}><rect x="8" y="8" width="12" height="12" rx="2" /><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" /></svg>
);
export const IconCheck = ({ size }: P) => (
  <svg {...base(size)}><path d="M5 12.5l4 4 10-10" /></svg>
);
export const IconSatellite = ({ size }: P) => (
  <svg {...base(size)}><path d="M5 19a7 7 0 0 1 0-10M9 15a3 3 0 0 1 0-2" /><circle cx="16" cy="8" r="3" /><path d="M13 11l-2 2" /></svg>
);
export const IconRefresh = ({ size }: P) => (
  <svg {...base(size)}><path d="M20 11a8 8 0 0 0-14-5L4 8M4 4v4h4" /><path d="M4 13a8 8 0 0 0 14 5l2-2M20 20v-4h-4" /></svg>
);
export const IconArrow = ({ size }: P) => (
  <svg {...base(size)}><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);
export const LogoMark = ({ size = 32 }: P) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
    <defs>
      <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#3b8ff0" />
        <stop offset="1" stopColor="#1c5cab" />
      </linearGradient>
    </defs>
    <rect width="64" height="64" rx="16" fill="url(#lg)" />
    <path d="M12 38c8 0 8-8 16-8s8 8 16 8 8-8 8-8" fill="none" stroke="#fff" strokeWidth="5" strokeLinecap="round" />
    <path d="M12 26c8 0 8-8 16-8s8 8 16 8" fill="none" stroke="#cde2fb" strokeWidth="4" strokeLinecap="round" />
  </svg>
);

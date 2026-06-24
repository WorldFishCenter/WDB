/**
 * A small, line-based icon set — replaces emoji chrome (📄 📊 🗒️ 🔍 ⚠️) with crisp SVG that
 * inherits `currentColor` and font-size, so icons sit on the type scale and read as considered
 * UI rather than placeholder glyphs. Stroke-based, 24-grid, 1.75 weight.
 */

export type IconName =
  | "doc" //    a source document (companion note / md / pdf)
  | "data" //   a dataset (CSV / table) — Mode C source
  | "note" //   a companion context note
  | "search" // refusal / not-found
  | "warn" //   unanswered
  | "graph" //  knowledge graph
  | "arrow" //  directed relation
  | "external"; // open source

const PATHS: Record<IconName, React.ReactNode> = {
  doc: (
    <>
      <path d="M13 2.5H6.5A1.5 1.5 0 0 0 5 4v16a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 20V8.5L13 2.5Z" />
      <path d="M13 2.5V8.5H19" />
      <path d="M8.5 13h7M8.5 16.5h7" />
    </>
  ),
  data: (
    <>
      <rect x="3.5" y="4.5" width="17" height="15" rx="1.5" />
      <path d="M3.5 9.5h17M3.5 14.5h17M9 9.5v10M15 9.5v10" />
    </>
  ),
  note: (
    <>
      <path d="M5 3.5h11.5L19 6v14.5a0 0 0 0 1 0 0H5A0 0 0 0 1 5 20.5V3.5Z" />
      <path d="M8 8h8M8 11.5h8M8 15h5" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M15.5 15.5 21 21" />
    </>
  ),
  warn: (
    <>
      <path d="M12 3.5 21.5 20H2.5L12 3.5Z" />
      <path d="M12 9.5v5M12 17.5h.01" />
    </>
  ),
  graph: (
    <>
      <circle cx="6" cy="18" r="2.5" />
      <circle cx="18" cy="17" r="2.5" />
      <circle cx="13" cy="6" r="2.5" />
      <path d="M8 16.2 11.4 8M14.7 7.6 16.7 14.8M8.3 17.2 15.6 16.6" />
    </>
  ),
  arrow: <path d="M5 12h13M13 6.5 18.5 12 13 17.5" />,
  external: (
    <>
      <path d="M14 4.5h5.5V10" />
      <path d="M19.5 4.5 11 13" />
      <path d="M18 14v4.5A1.5 1.5 0 0 1 16.5 20H6A1.5 1.5 0 0 1 4.5 18.5V8A1.5 1.5 0 0 1 6 6.5h4" />
    </>
  ),
};

export function Icon({
  name,
  size = "1.05em",
  className,
}: {
  name: IconName;
  size?: number | string;
  className?: string;
}) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ flex: "none", display: "block" }}
    >
      {PATHS[name]}
    </svg>
  );
}

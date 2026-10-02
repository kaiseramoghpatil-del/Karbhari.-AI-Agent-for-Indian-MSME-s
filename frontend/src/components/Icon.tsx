const PATHS: Record<string, string> = {
  findings: 'M12 3v3m0 12v3M3 12h3m12 0h3M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  investigation: 'M5 3h14v18H5zM8 7h8M8 11h2m3 0h3M8 15h2m3 0h3M8 19h8',
  evidence: 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6',
  trace: 'M6 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM18 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM6 8v4a4 4 0 0 0 4 4h6',
  actions: 'M13 2 4 14h7l-1 8 9-12h-7z',
  sound: 'M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11',
  mute: 'M4 9v6h4l5 4V5L8 9zM17 9l5 6m0-6-5 6',
  upload: 'M12 16V4m-5 5 5-5 5 5M4 16v4h16v-4',
  play: 'M7 4v16l13-8z',
  back: 'M15 5l-7 7 7 7',
  check: 'M4 12l5 5L20 6',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
  bank: 'M3 10h18M5 10v8m4-8v8m6-8v8m4-8v8M3 20h18M12 3l9 5H3z',
  spark: 'M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z',
  doc: 'M7 3h7l5 5v13H7zM14 3v5h5',
  x: 'M6 6l12 12M18 6 6 18',
}

export function Icon({ name, size = 18, className = '' }: { name: keyof typeof PATHS | string; size?: number; className?: string }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name] ?? PATHS.spark} />
    </svg>
  )
}

/**
 * Logo — BMW OpenCode wordmark for the web frontend header.
 *
 * Renders the galaxy icon (inlined SVG so no network request) alongside
 * the "OpenCode" wordmark with BMW colour tokens.  Accepts an optional
 * `size` prop ("sm" | "md") for toolbar vs. splash-screen use.
 */

interface LogoProps {
  /** "sm" = compact toolbar lockup (default); "md" = larger splash / login screen */
  size?: "sm" | "md";
  className?: string;
}

export function Logo({ size = "sm", className = "" }: LogoProps) {
  const iconSize  = size === "sm" ? 22 : 36;
  const textClass = size === "sm"
    ? "text-sm font-semibold tracking-tight"
    : "text-xl font-bold    tracking-tight";

  return (
    <div className={`flex items-center gap-2 select-none ${className}`}>
      {/* Galaxy icon — inline so it inherits correct sizing and no FOUC */}
      <svg
        width={iconSize}
        height={iconSize}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="logo-bg" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#1a2035" />
            <stop offset="100%" stopColor="#0a0d14" />
          </radialGradient>
          <radialGradient id="logo-core" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#5b9cf6" stopOpacity="1" />
            <stop offset="60%"  stopColor="#1c69d4" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0653b6" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="logo-ring" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stopColor="#1c69d4" stopOpacity="0.9" />
            <stop offset="50%"  stopColor="#5b9cf6" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#1c69d4" stopOpacity="0.1" />
          </linearGradient>
          <filter id="logo-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="1.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="logo-core-filter" x="-80%" y="-80%" width="360%" height="360%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background pill */}
        <rect width="64" height="64" rx="14" fill="url(#logo-bg)" />

        {/* Orbit rings */}
        <ellipse cx="32" cy="32" rx="22" ry="9" fill="none"
          stroke="url(#logo-ring)" strokeWidth="0.8" opacity="0.7"
          transform="rotate(-30 32 32)" />
        <ellipse cx="32" cy="32" rx="22" ry="9" fill="none"
          stroke="url(#logo-ring)" strokeWidth="0.5" opacity="0.35"
          transform="rotate(60 32 32)" />

        {/* Connection lines */}
        <line x1="32" y1="32" x2="52" y2="22" stroke="#1c69d4" strokeWidth="0.6" opacity="0.5" />
        <line x1="32" y1="32" x2="14" y2="44" stroke="#1c69d4" strokeWidth="0.6" opacity="0.5" />
        <line x1="32" y1="32" x2="46" y2="50" stroke="#5b9cf6" strokeWidth="0.6" opacity="0.35" />
        <line x1="32" y1="32" x2="16" y2="18" stroke="#5b9cf6" strokeWidth="0.6" opacity="0.35" />

        {/* Core glow + node */}
        <circle cx="32" cy="32" r="10" fill="url(#logo-core)" opacity="0.5" />
        <circle cx="32" cy="32" r="5.5" fill="#1c69d4" filter="url(#logo-core-filter)" />
        <circle cx="32" cy="32" r="3.5" fill="#5b9cf6" />
        <circle cx="32" cy="32" r="1.8" fill="#e8f0ff" />

        {/* Satellite nodes */}
        <circle cx="52" cy="22" r="2.2" fill="#1c69d4" filter="url(#logo-glow)" />
        <circle cx="52" cy="22" r="1.2" fill="#5b9cf6" />
        <circle cx="14" cy="44" r="2.2" fill="#1c69d4" filter="url(#logo-glow)" />
        <circle cx="14" cy="44" r="1.2" fill="#5b9cf6" />
        <circle cx="46" cy="50" r="1.6" fill="#0e4fa8" filter="url(#logo-glow)" />
        <circle cx="46" cy="50" r="0.9" fill="#3a7fd4" />
        <circle cx="16" cy="18" r="1.6" fill="#0e4fa8" filter="url(#logo-glow)" />
        <circle cx="16" cy="18" r="0.9" fill="#3a7fd4" />

        {/* Star dust */}
        <circle cx="42" cy="13" r="0.6" fill="#5b9cf6" opacity="0.6" />
        <circle cx="56" cy="38" r="0.5" fill="#5b9cf6" opacity="0.4" />
        <circle cx="8"  cy="30" r="0.5" fill="#5b9cf6" opacity="0.4" />
        <circle cx="22" cy="56" r="0.6" fill="#5b9cf6" opacity="0.5" />
        <circle cx="58" cy="14" r="0.4" fill="#9bbff5" opacity="0.5" />
        <circle cx="6"  cy="52" r="0.4" fill="#9bbff5" opacity="0.4" />
      </svg>

      {/* Wordmark */}
      <span className={textClass} aria-label="OpenCode">
        <span className="text-bmw-blue-light">Open</span>
        <span className="text-white">Code</span>
      </span>
    </div>
  );
}

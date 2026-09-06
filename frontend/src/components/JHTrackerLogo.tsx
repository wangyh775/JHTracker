import React from 'react';

interface JHTrackerLogoProps {
  size?: number;
  className?: string;
  animated?: boolean;
  showCenterDot?: boolean;
}

/**
 * JHTracker Dynamic Kinetic Logo
 * - Zero glow, crisp vector aesthetics
 * - Hardware-accelerated GPU CSS keyframes
 * - Interactive hover spin acceleration
 */
export const JHTrackerLogo: React.FC<JHTrackerLogoProps> = ({
  size = 32,
  className = '',
  animated = true,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 320 320"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`group select-none transition-transform duration-300 hover:scale-105 ${className}`}
      role="img"
      aria-label="JHTracker Kinetic Logo"
    >
      <defs>
        <linearGradient id="jhtLogoStreamCyan" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="50%" stopColor="#0284c7" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>

        <linearGradient id="jhtLogoStreamPurple" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#c084fc" />
          <stop offset="50%" stopColor="#7e22ce" />
          <stop offset="100%" stopColor="#0284c7" />
        </linearGradient>
      </defs>

      {/* Solid Outer Bezel */}
      <rect width="320" height="320" rx="64" fill="#080c16" stroke="#1e293b" strokeWidth="2.5" />
      <rect x="8" y="8" width="304" height="304" rx="56" fill="#060911" stroke="#334155" strokeWidth="1.2" strokeOpacity="0.8" />

      {/* Counter-Clockwise Tactical Dial */}
      <g
        className={animated ? 'origin-center animate-[spin_36s_linear_infinite] group-hover:animate-[spin_10s_linear_infinite]' : ''}
        style={{ transformOrigin: '160px 160px' }}
      >
        <circle cx="160" cy="160" r="142" fill="none" stroke="#334155" strokeWidth="1.2" strokeDasharray="3 7" />
        <circle cx="160" cy="18" r="3" fill="#38bdf8" />
        <circle cx="160" cy="302" r="3" fill="#38bdf8" />
        <circle cx="18" cy="160" r="3" fill="#38bdf8" />
        <circle cx="302" cy="160" r="3" fill="#38bdf8" />
      </g>

      {/* Clockwise Radar Crosshair Axis */}
      <g
        className={animated ? 'origin-center animate-[spin_24s_linear_infinite] group-hover:animate-[spin_8s_linear_infinite]' : ''}
        style={{ transformOrigin: '160px 160px' }}
      >
        <circle cx="160" cy="160" r="126" fill="none" stroke="#1e293b" strokeWidth="1.5" />
        <line x1="160" y1="34" x2="160" y2="44" stroke="#38bdf8" strokeWidth="2" />
        <line x1="160" y1="276" x2="160" y2="286" stroke="#38bdf8" strokeWidth="2" />
        <line x1="34" y1="160" x2="44" y2="160" stroke="#38bdf8" strokeWidth="2" />
        <line x1="276" y1="160" x2="286" y2="160" stroke="#38bdf8" strokeWidth="2" />
      </g>

      {/* Static Base Rails */}
      <path d="M 160 160 C 130 96, 68 96, 68 160 C 68 224, 130 224, 160 160" fill="none" stroke="#0f172a" strokeWidth="14" strokeLinecap="round" />
      <path d="M 160 160 C 130 96, 68 96, 68 160 C 68 224, 130 224, 160 160" fill="none" stroke="url(#jhtLogoStreamCyan)" strokeWidth="10" strokeLinecap="round" opacity="0.6" />

      <path d="M 160 160 C 190 224, 252 224, 252 160 C 252 96, 190 96, 160 160" fill="none" stroke="#0f172a" strokeWidth="14" strokeLinecap="round" />
      <path d="M 160 160 C 190 224, 252 224, 252 160 C 252 96, 190 96, 160 160" fill="none" stroke="url(#jhtLogoStreamPurple)" strokeWidth="10" strokeLinecap="round" opacity="0.6" />

      {/* High-Speed Kinetic Pulses */}
      <path
        d="M 160 160 C 130 96, 68 96, 68 160 C 68 224, 130 224, 160 160"
        fill="none"
        stroke="#ffffff"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeDasharray="12 18"
        className={animated ? 'jht-pulse-l' : ''}
      />
      <path
        d="M 160 160 C 190 224, 252 224, 252 160 C 252 96, 190 96, 160 160"
        fill="none"
        stroke="#ffffff"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeDasharray="12 18"
        className={animated ? 'jht-pulse-r' : ''}
      />

      {/* Physical Bridge Gap Notch */}
      <circle cx="160" cy="160" r="23" fill="#060911" stroke="#1e293b" strokeWidth="2" />

      {/* Core Quantum Diamond Target */}
      <g
        className={animated ? 'origin-center animate-[pulse_4s_ease-in-out_infinite]' : ''}
        style={{ transformOrigin: '160px 160px' }}
      >
        <polygon points="160,146 174,160 160,174 146,160" fill="#38bdf8" />
        <polygon points="160,150 170,160 160,170 150,160" fill="#ffffff" />
        <circle cx="160" cy="160" r="3.5" fill="#060911" />
      </g>

      {/* J & H Monogram Nodes */}
      <circle cx="86" cy="192" r="4.5" fill="#38bdf8" stroke="#060911" strokeWidth="2" />
      <path d="M 86 192 L 86 212 C 86 220 78 224 70 224" fill="none" stroke="#38bdf8" strokeWidth="3" strokeLinecap="round" />

      <circle cx="234" cy="128" r="4.5" fill="#c084fc" stroke="#060911" strokeWidth="2" />
      <line x1="234" y1="128" x2="234" y2="104" stroke="#c084fc" strokeWidth="3" strokeLinecap="round" />
      <line x1="245" y1="128" x2="245" y2="104" stroke="#c084fc" strokeWidth="3" strokeLinecap="round" />
      <line x1="234" y1="116" x2="245" y2="116" stroke="#c084fc" strokeWidth="2" />
    </svg>
  );
};

export default JHTrackerLogo;

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        none: '0px',
        DEFAULT: '2px',
        sm: '2px',
        md: '2px',
        lg: '2px',
        xl: '2px',
        full: '9999px',
      },
      spacing: {
        0: '0px',
        1: '4px',
        2: '8px',
        3: '12px',
        4: '16px',
        5: '20px',
        6: '24px',
        8: '32px',
        10: '40px',
        12: '48px',
        16: '64px',
        20: '80px',
        24: '96px',
        px: '1px',
      },
      fontSize: {
        xs: ['12px', { lineHeight: '1.5' }],
        sm: ['14px', { lineHeight: '1.5' }],
        base: ['16px', { lineHeight: '1.5' }],
        lg: ['20px', { lineHeight: '1.4' }],
        xl: ['28px', { lineHeight: '1.2' }],
        '2xl': ['44px', { lineHeight: '1.0' }],
        '3xl': ['64px', { lineHeight: '0.95' }],
      },
      colors: {
        bg: "#17140F",
        paper: "#F5EFE0",
        ink: "#2B2620",
        stamp: "#E8422D",
        "stamp-hover": "#D43723",
        ember: "#FFB93C",
        tan: "#C9BFA6",
        "tan-dim": "#8A8168",
        success: "#7FA65C",
      },
      fontFamily: {
        display: ['"Archivo Black"', "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ['"IBM Plex Mono"', "monospace"],
        handwritten: ['"Caveat"', "cursive"],
      },
      lineHeight: {
        tight: '0.98',
        display: '1.02',
      },
      boxShadow: {
        paper: "0 30px 60px rgba(0,0,0,0.45)",
      },
      keyframes: {
        stampEntrance: {
          '0%': {
            transform: 'scale(2.2) rotate(var(--stamp-rotate, -12deg))',
            opacity: '0',
          },
          '60%': {
            transform: 'scale(0.92) rotate(var(--stamp-rotate, -12deg))',
            opacity: '1',
          },
          '100%': {
            transform: 'scale(1) rotate(var(--stamp-rotate, -12deg))',
            opacity: '1',
          },
        },
        penMark: {
          '0%': {
            strokeDashoffset: '100',
            opacity: '0',
          },
          '100%': {
            strokeDashoffset: '0',
            opacity: '1',
          },
        },
        paperSettle: {
          '0%': {
            opacity: '0',
            transform: 'translateY(16px) rotate(0deg)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0) rotate(var(--paper-rotate, -1.5deg))',
          },
        },
      },
      animation: {
        'stamp-slam': 'stampEntrance 500ms cubic-bezier(.2, 1.4, .4, 1) forwards',
        'paper-settle': 'paperSettle 350ms ease-out forwards',
      },
    },
  },
  plugins: [],
};

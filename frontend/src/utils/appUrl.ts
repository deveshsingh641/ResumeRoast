/**
 * Utility to get canonical live web app base URL.
 * Automatically adapts between local development, Vercel deployments,
 * and custom environment overrides without hardcoding.
 */
export function getAppUrl(): string {
  if (import.meta.env.VITE_APP_URL) {
    return (import.meta.env.VITE_APP_URL as string).replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin.replace(/\/$/, "");
  }
  return "https://resume-roast-lemon.vercel.app";
}

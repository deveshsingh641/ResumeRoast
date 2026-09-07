import { useEffect } from "react";

/**
 * Custom hook to dynamically update document title and reset on unmount.
 */
export function usePageTitle(title: string) {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = `${title} | Resume Roast`;
    return () => {
      document.title = prevTitle;
    };
  }, [title]);
}

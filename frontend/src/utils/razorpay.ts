/**
 * Razorpay SDK Dynamic Loader & TypeScript Types
 * Provides secure in-page Checkout overlay for Indian UPI, QR, Netbanking, and Cards.
 */

export interface RazorpaySuccessResponse {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

export interface RazorpayFailureResponse {
  error: {
    code: string;
    description: string;
    source: string;
    step: string;
    reason: string;
    metadata: {
      order_id: string;
      payment_id?: string;
    };
  };
}

export interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description?: string;
  image?: string;
  order_id: string;
  handler: (response: RazorpaySuccessResponse) => void;
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  notes?: Record<string, string>;
  theme?: {
    color?: string;
    backdrop_color?: string;
  };
  modal?: {
    ondismiss?: () => void;
    escape?: boolean;
    backdropclose?: boolean;
    confirm_close?: boolean;
  };
  config?: {
    display?: {
      blocks?: Record<string, any>;
      sequence?: string[];
      preferences?: {
        show_default_blocks?: boolean;
      };
    };
  };
}

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => {
      open: () => void;
      on: (event: string, handler: (response: any) => void) => void;
      close: () => void;
    };
  }
}

let loadPromise: Promise<boolean> | null = null;

/**
 * Dynamically loads Razorpay's official checkout.js SDK into the page.
 * Cached so multiple calls reuse the same script, but resets on failure to allow clean retries.
 */
export function loadRazorpaySDK(): Promise<boolean> {
  if (typeof window === "undefined") {
    return Promise.resolve(false);
  }

  if (window.Razorpay) {
    return Promise.resolve(true);
  }

  if (loadPromise) {
    return loadPromise;
  }

  loadPromise = new Promise<boolean>((resolve) => {
    // 1. If window.Razorpay already initialized, resolve immediately
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    // 2. Check if script element already exists in document
    const existingScript = document.querySelector<HTMLScriptElement>(
      'script[src="https://checkout.razorpay.com/v1/checkout.js"]',
    );

    if (existingScript) {
      // Check readyState if available
      const anyScript = existingScript as any;
      if (
        anyScript.readyState === "loaded" ||
        anyScript.readyState === "complete"
      ) {
        if (window.Razorpay) {
          resolve(true);
          return;
        }
      }

      existingScript.addEventListener("load", () => {
        resolve(Boolean(window.Razorpay));
      });
      existingScript.addEventListener("error", () => {
        loadPromise = null;
        resolve(false);
      });

      // Poll with 50ms interval for up to 5 seconds
      let checkCount = 0;
      const interval = setInterval(() => {
        checkCount++;
        if (window.Razorpay) {
          clearInterval(interval);
          resolve(true);
        } else if (checkCount > 100) {
          // 5 seconds max
          clearInterval(interval);
          const isAvailable = Boolean(window.Razorpay);
          if (!isAvailable) {
            loadPromise = null; // allow retry
          }
          resolve(isAvailable);
        }
      }, 50);

      return;
    }

    // 3. If no script tag exists, inject one
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(Boolean(window.Razorpay));
    script.onerror = () => {
      console.error("Failed to load Razorpay Checkout SDK.");
      loadPromise = null; // allow retry
      resolve(false);
    };
    document.body.appendChild(script);
  });

  return loadPromise;
}

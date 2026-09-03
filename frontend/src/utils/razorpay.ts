/**
 * Razorpay SDK Dynamic Loader & TypeScript Types
 * Provides secure in-page Checkout overlay for Indian UPI, QR, Netbanking, and Cards.
 */

export interface RazorpaySuccessResponse {
  razorpay_payment_id: string
  razorpay_order_id: string
  razorpay_signature: string
}

export interface RazorpayFailureResponse {
  error: {
    code: string
    description: string
    source: string
    step: string
    reason: string
    metadata: {
      order_id: string
      payment_id?: string
    }
  }
}

export interface RazorpayOptions {
  key: string
  amount: number
  currency: string
  name: string
  description?: string
  image?: string
  order_id: string
  handler: (response: RazorpaySuccessResponse) => void
  prefill?: {
    name?: string
    email?: string
    contact?: string
  }
  notes?: Record<string, string>
  theme?: {
    color?: string
    backdrop_color?: string
  }
  modal?: {
    ondismiss?: () => void
    escape?: boolean
    backdropclose?: boolean
    confirm_close?: boolean
  }
  config?: {
    display?: {
      blocks?: Record<string, any>
      sequence?: string[]
      preferences?: {
        show_default_blocks?: boolean
      }
    }
  }
}

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => {
      open: () => void
      on: (event: string, handler: (response: any) => void) => void
      close: () => void
    }
  }
}

let loadPromise: Promise<boolean> | null = null

/**
 * Dynamically loads Razorpay's official checkout.js SDK into the page.
 * Cached so multiple calls reuse the same script.
 */
export function loadRazorpaySDK(): Promise<boolean> {
  if (typeof window === 'undefined') {
    return Promise.resolve(false)
  }

  if (window.Razorpay) {
    return Promise.resolve(true)
  }

  if (loadPromise) {
    return loadPromise
  }

  loadPromise = new Promise<boolean>((resolve) => {
    // Check if script element already exists in document
    const existingScript = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]')
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(true))
      existingScript.addEventListener('error', () => resolve(false))
      return
    }

    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.onload = () => resolve(true)
    script.onerror = () => {
      console.error('Failed to load Razorpay Checkout SDK.')
      resolve(false)
    }
    document.body.appendChild(script)
  })

  return loadPromise
}

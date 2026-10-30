import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./index.css";
import "./i18n";
import { getCurrentLanguage } from "./i18n";
import App from "./App";

import { useAppStore } from "./store/useAppStore";

if (typeof window !== "undefined") {
  window.addEventListener("unhandledrejection", (event) => {
    console.warn("Unhandled promise rejection captured:", event.reason);
  });
}

if (import.meta.env.VITE_API_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_URL;
}

axios.defaults.withCredentials = true;

// Ingest pro_token from URL (?pro_token=... or ?token=...) on app boot (Magic link/restore flow)
if (typeof window !== "undefined") {
  try {
    const searchParams = new URLSearchParams(window.location.search);
    const tokenParam =
      searchParams.get("pro_token") || searchParams.get("token");
    if (tokenParam && tokenParam.trim()) {
      const cleanToken = tokenParam.trim();
      localStorage.setItem("resumeroast_pro_token", cleanToken);
      sessionStorage.setItem("resumeroast_pro_token", cleanToken);
      searchParams.delete("pro_token");
      searchParams.delete("token");
      const cleanQuery = searchParams.toString();
      const cleanUrl =
        window.location.pathname +
        (cleanQuery ? `?${cleanQuery}` : "") +
        window.location.hash;
      window.history.replaceState({}, document.title, cleanUrl);
    }
    const emailParam = searchParams.get("email");
    if (emailParam && emailParam.trim()) {
      localStorage.setItem(
        "resumeroast_user_email",
        emailParam.trim().toLowerCase(),
      );
    }
  } catch {}
}

// Attach authentication tokens (Pro token, Founder admin key, email, language) to API requests
axios.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  try {
    const userEmail = localStorage.getItem("resumeroast_user_email");
    if (userEmail) {
      config.headers["X-User-Email"] = userEmail;
    }

    const proToken =
      localStorage.getItem("resumeroast_pro_token") ||
      sessionStorage.getItem("resumeroast_pro_token");
    if (proToken) {
      config.headers["X-Pro-Token"] = proToken;
    }

    const adminKey =
      sessionStorage.getItem("rr_admin_key") ||
      localStorage.getItem("rr_admin_key");
    if (adminKey) {
      config.headers["X-Admin-Key"] = adminKey;
    }

    config.headers["X-Language"] = getCurrentLanguage();
  } catch {}
  return config;
});

// Sync usage and Pro entitlement on initial boot (with auto-restore for paying users)
try {
  const savedEmail =
    typeof window !== "undefined"
      ? localStorage.getItem("resumeroast_user_email")
      : null;
  const savedToken =
    typeof window !== "undefined"
      ? localStorage.getItem("resumeroast_pro_token") ||
        sessionStorage.getItem("resumeroast_pro_token")
      : null;

  if (savedEmail) {
    useAppStore.getState().setUserEmail(savedEmail);
  }

  if (savedEmail && !savedToken) {
    // If email is saved but token was lost (e.g. mobile payment redirect/restart), restore token silently
    axios
      .post("/api/auth/login", { email: savedEmail })
      .then((authRes) => {
        if (authRes.data && authRes.data.token) {
          localStorage.setItem("resumeroast_pro_token", authRes.data.token);
          sessionStorage.setItem("resumeroast_pro_token", authRes.data.token);
        }
        if (authRes.data && authRes.data.is_pro) {
          useAppStore.getState().setUsage({
            used: 0,
            remaining: 999999,
            limit: 999999,
            is_pro: true,
          });
        }
        return axios.get("/api/usage");
      })
      .then((usageRes) => {
        if (usageRes && usageRes.data) {
          if (usageRes.data.token) {
            localStorage.setItem("resumeroast_pro_token", usageRes.data.token);
            sessionStorage.setItem(
              "resumeroast_pro_token",
              usageRes.data.token,
            );
          }
          if (usageRes.data.email) {
            useAppStore.getState().setUserEmail(usageRes.data.email);
          }
          useAppStore.getState().setUsage(usageRes.data);
        }
      })
      .catch(() => {
        axios
          .get("/api/usage")
          .then((res) => {
            if (res.data) {
              if (res.data.token) {
                localStorage.setItem("resumeroast_pro_token", res.data.token);
                sessionStorage.setItem("resumeroast_pro_token", res.data.token);
              }
              if (res.data.email) {
                useAppStore.getState().setUserEmail(res.data.email);
              }
              useAppStore.getState().setUsage(res.data);
            }
          })
          .catch(() => {});
      });
  } else {
    axios
      .get("/api/usage")
      .then((res) => {
        if (res.data) {
          if (res.data.token) {
            localStorage.setItem("resumeroast_pro_token", res.data.token);
            sessionStorage.setItem("resumeroast_pro_token", res.data.token);
          }
          if (res.data.email) {
            useAppStore.getState().setUserEmail(res.data.email);
          }
          useAppStore.getState().setUsage(res.data);
        }
      })
      .catch(() => {});
  }
} catch {}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

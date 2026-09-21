import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./index.css";
import "./i18n";
import { getCurrentLanguage } from "./i18n";
import App from "./App";

import { useAppStore } from "./store/useAppStore";

if (import.meta.env.VITE_API_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_URL;
}

axios.defaults.withCredentials = true;

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

// Sync usage and Pro entitlement on initial boot
try {
  axios
    .get("/api/usage")
    .then((res) => {
      if (res.data) {
        useAppStore.getState().setUsage(res.data);
      }
    })
    .catch(() => {});
} catch {}


createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

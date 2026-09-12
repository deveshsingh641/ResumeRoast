import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./index.css";
import "./i18n";
import { getCurrentLanguage } from "./i18n";
import App from "./App";

if (import.meta.env.VITE_API_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_URL;
}

axios.defaults.withCredentials = true;

// Automatically attach authenticated Pro token, user email and current language preference to API requests
axios.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  try {
    const proToken = localStorage.getItem("resumeroast_pro_token");
    if (proToken) {
      config.headers["X-Pro-Token"] = proToken;
    }
    const userEmail = localStorage.getItem("resumeroast_user_email");
    if (userEmail) {
      config.headers["X-User-Email"] = userEmail;
    }
    config.headers["X-Language"] = getCurrentLanguage();
  } catch {}
  return config;
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

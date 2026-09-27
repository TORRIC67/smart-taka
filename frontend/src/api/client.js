import { t } from "../i18n";

// src/api/client.js - the ONE place that talks to the backend.
// Adds the login token to every request and turns errors into readable messages.

const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => (t ? localStorage.setItem("token", t) : localStorage.removeItem("token"));

export async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  // JSON bodies get a JSON header. The login form (URLSearchParams) sets its own.
  if (options.body && !(options.body instanceof URLSearchParams)) headers["Content-Type"] = "application/json";

  let res;
  try {
    res = await fetch(`${API}${path}`, { ...options, headers });
  } catch {
    const err = new Error(t("server_unreachable"));
    err.status = 0;
    throw err;
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // FastAPI sends errors in `detail` (text, or a list for validation errors)
    let msg = data.detail;
    if (Array.isArray(msg)) msg = msg.map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`).join("; ");
    else if (msg && typeof msg === "object") msg = JSON.stringify(msg);
    if (res.status === 401 && token) window.dispatchEvent(new Event("auth-expired")); // token expired -> logout
    const err = new Error(msg || `Request failed (${res.status})`);
    err.status = res.status; // 409 = already paid, 403 = not allowed ...
    throw err;
  }
  return data;
}

export const get = (path) => request(path);
export const post = (path, body) => request(path, { method: "POST", body: JSON.stringify(body ?? {}) });
export const patch = (path, body) => request(path, { method: "PATCH", body: JSON.stringify(body ?? {}) });
export const del = (path) => request(path, { method: "DELETE" });

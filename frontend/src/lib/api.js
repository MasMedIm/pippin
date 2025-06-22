// Utility wrapper around fetch that automatically resolves the correct backend
// base URL whether we are:
//  1. Running `npm run dev` (Vite dev-server with proxy)
//  2. Using the production build served on port 5173 (no proxy)
//  3. Deployed behind another origin (set VITE_API_BASE_URL)

function resolveApiBase() {
  // Highest priority: explicit env variable (set at build-time)
  const env = import.meta.env.VITE_API_BASE_URL;
  if (env) return env.replace(/\/$/, ""); // strip trailing slash

  // If we are on port 5173 (default dev & prod container), assume backend on 8000.
  if (window.location.port === "5173") {
    return `${window.location.protocol}//${window.location.hostname}:8000/api`;
  }

  // Fallback – same origin path prefix (works with Vite proxy in dev)
  return "/api";
}

const API_BASE = resolveApiBase();

export async function apiFetch(path, options = {}) {
  // Inject Authorization header if access token is present
  const token = localStorage.getItem('access_token');
  const headers = { ...(options.headers || {}) };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${options.method || "GET"} ${path} failed: ${res.status} – ${text}`);
  }
  return res;
}

export async function fetchHealth() {
  const res = await apiFetch("/health");
  return res.json();
}

export async function fetchEphemeralSession({ voice } = {}) {
  const res = await apiFetch("/realtime/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ voice }),
  });
  return res.json();
}
/**
 * Authenticate user and retrieve JWT token.
 * @param {{email: string, password: string}} params
 * @returns {Promise<{ access_token: string, token_type: string }>}
 */
export async function loginUser({ email, password }) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Login failed: ${res.status} – ${text}`);
  }
  return res.json();
}
/**
 * Register a new user.
 * @param {{email: string, password: string, fullName: string}} params
 * @returns {Promise<Object>}
 */
export async function registerUser({ email, password, fullName }) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Register failed: ${res.status} – ${text}`);
  }
  return res.json();
}

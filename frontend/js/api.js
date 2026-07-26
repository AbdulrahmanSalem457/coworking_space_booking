/**
 * api.js — every network call the frontend makes lives here.
 * Nothing in dom.js or the page scripts talks to fetch() directly.
 */

/**
 * Where the API lives.
 *
 * Served from localhost it talks to a local backend; served from anywhere else
 * it falls back to the hosted one. Point it somewhere specific by setting the
 * global before this module loads:
 *
 *   <script>window.API_BASE_URL = "https://username.pythonanywhere.com/api";</script>
 *
 * After deploying, change HOSTED_API_URL below to your own API's address.
 */
const HOSTED_API_URL = "https://s3ody.pythonanywhere.com/api";
const LOCAL_API_URL = "http://127.0.0.1:8000/api";

const isLocalHost = ["localhost", "127.0.0.1", ""].includes(window.location.hostname);
const API_BASE_URL = window.API_BASE_URL ?? (isLocalHost ? LOCAL_API_URL : HOSTED_API_URL);

const TOKEN_KEYS = { access: "csb_access_token", refresh: "csb_refresh_token", username: "csb_username" };

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEYS.access);
}

export function getUsername() {
  return localStorage.getItem(TOKEN_KEYS.username);
}

export function isLoggedIn() {
  return Boolean(getAccessToken());
}

function setSession({ access, refresh, username }) {
  if (access) localStorage.setItem(TOKEN_KEYS.access, access);
  if (refresh) localStorage.setItem(TOKEN_KEYS.refresh, refresh);
  if (username) localStorage.setItem(TOKEN_KEYS.username, username);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEYS.access);
  localStorage.removeItem(TOKEN_KEYS.refresh);
  localStorage.removeItem(TOKEN_KEYS.username);
}

/** Flattens DRF-style error payloads ({field: [msg]} or {non_field_errors: [...]}) into one line. */
function flattenApiErrors(data) {
  if (!data || typeof data !== "object") return "Something went wrong. Please try again.";
  if (typeof data.detail === "string") return data.detail;

  const parts = [];
  for (const [field, value] of Object.entries(data)) {
    const message = Array.isArray(value) ? value.join(" ") : String(value);
    parts.push(field === "non_field_errors" ? message : `${field}: ${message}`);
  }
  return parts.join(" ") || "Something went wrong. Please try again.";
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem(TOKEN_KEYS.refresh);
  if (!refresh) return false;

  const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) return false;

  const data = await response.json();
  setSession({ access: data.access });
  return true;
}

/**
 * Core fetch wrapper: attaches JSON headers + the JWT bearer token, retries
 * once on a 401 after refreshing the access token, and throws ApiError with
 * a human-readable message on any non-2xx response.
 */
async function request(path, { method = "GET", body, auth = true, isRetry = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && getAccessToken()) {
    headers.Authorization = `Bearer ${getAccessToken()}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth && !isRetry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return request(path, { method, body, auth, isRetry: true });
    clearSession();
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(flattenApiErrors(data), response.status, data);
  }
  return data;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function registerUser({ username, email, password, passwordConfirm }) {
  return request("/auth/register/", {
    auth: false,
    method: "POST",
    body: { username, email, password, password_confirm: passwordConfirm },
  });
}

export async function loginUser({ username, password }) {
  const data = await request("/auth/login/", { auth: false, method: "POST", body: { username, password } });
  setSession({ access: data.access, refresh: data.refresh, username });
  return data;
}

export function logoutUser() {
  clearSession();
}

// ---------------------------------------------------------------------------
// Spaces
// ---------------------------------------------------------------------------

export async function fetchSpaces({ search = "", capacity = "" } = {}) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (capacity) params.set("capacity", capacity);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/spaces/${query}`, { auth: false });
}

export async function fetchSpace(slug) {
  return request(`/spaces/${slug}/`, { auth: false });
}

// ---------------------------------------------------------------------------
// Bookings
// ---------------------------------------------------------------------------

export async function createBooking({ spaceSlug, date, startTime, endTime }) {
  return request("/bookings/", {
    method: "POST",
    body: { space: spaceSlug, date, start_time: startTime, end_time: endTime },
  });
}

export async function fetchMyBookings() {
  return request("/bookings/");
}

export async function cancelBooking(id) {
  return request(`/bookings/${id}/`, { method: "DELETE" });
}

export const PAYMENT_METHODS = [
  { value: "cash", label: "Cash" },
  { value: "credit_card", label: "Credit Card" },
  { value: "debit_card", label: "Debit Card" },
  { value: "wallet", label: "Digital Wallet" },
  { value: "bank_transfer", label: "Bank Transfer" },
];

export async function checkInBooking(id) {
  return request(`/bookings/${id}/check-in/`, { method: "POST" });
}

export async function checkOutBooking(id, paymentMethod) {
  return request(`/bookings/${id}/check-out/`, {
    method: "POST",
    body: { payment_method: paymentMethod },
  });
}

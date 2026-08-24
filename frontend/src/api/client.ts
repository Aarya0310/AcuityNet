import type { VitalObservation } from "../contracts/vitals";
import type { AutomaticRefreshInterval, RefreshConfiguration } from "../contracts/configuration";
import type { Prediction } from "../contracts/predictions";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
let accessToken: string | null = localStorage.getItem("acuitynet.access_token");

export type AuthUser = { user_id: string; username: string; display_name: string; role: "admin" | "doctor" | "nurse" };
export type Session = { access_token: string; token_type: "bearer"; expires_in: number; user: AuthUser };
export function clearSession() { accessToken = null; localStorage.removeItem("acuitynet.access_token"); }
export async function login(username: string, password: string): Promise<Session> {
  const session = await getJson<Session>("/api/v1/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) });
  accessToken = session.access_token; localStorage.setItem("acuitynet.access_token", accessToken); return session;
}
export async function getCurrentUser(): Promise<AuthUser> { return getJson<AuthUser>("/api/v1/auth/me"); }
export async function logout(): Promise<void> { try { await getJson<void>("/api/v1/auth/logout", { method: "POST" }); } finally { clearSession(); } }
export function getPrediction(patientId: string): Promise<Prediction> { return getJson<Prediction>(`/api/v1/patients/${encodeURIComponent(patientId)}/prediction`); }

export async function getCurrentVitals(patientId: string): Promise<VitalObservation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/patients/${encodeURIComponent(patientId)}/vitals/current`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(`Current vitals request failed with status ${response.status}`);
  }
  return (await response.json()) as VitalObservation;
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers: { ...authHeaders(), ...init?.headers } });
  if (response.status === 401) clearSession();
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}
function authHeaders(): HeadersInit { return accessToken ? { Authorization: `Bearer ${accessToken}` } : {}; }

export function getRefreshConfiguration(): Promise<RefreshConfiguration> {
  return getJson<RefreshConfiguration>("/api/v1/configuration");
}

export function advanceVitals(patientId: string, interval: AutomaticRefreshInterval): Promise<VitalObservation> {
  return getJson<VitalObservation>(`/api/v1/patients/${encodeURIComponent(patientId)}/vitals/advance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ interval }),
  });
}

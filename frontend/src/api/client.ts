import type { VitalObservation } from "../contracts/vitals";
import type { AutomaticRefreshInterval, RefreshConfiguration } from "../contracts/configuration";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getCurrentVitals(patientId: string): Promise<VitalObservation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/patients/${encodeURIComponent(patientId)}/vitals/current`);
  if (!response.ok) {
    throw new Error(`Current vitals request failed with status ${response.status}`);
  }
  return (await response.json()) as VitalObservation;
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

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

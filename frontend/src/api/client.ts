import type { VitalObservation } from "../contracts/vitals";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getCurrentVitals(patientId: string): Promise<VitalObservation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/patients/${encodeURIComponent(patientId)}/vitals/current`);
  if (!response.ok) {
    throw new Error(`Current vitals request failed with status ${response.status}`);
  }
  return (await response.json()) as VitalObservation;
}

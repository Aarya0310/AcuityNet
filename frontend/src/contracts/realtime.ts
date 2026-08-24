export type OperationalState =
  | "loading"
  | "stale"
  | "disconnected"
  | "unavailable_fallback"
  | "no_active_alert"
  | "no_candidate"
  | "not_yet_available";

export type RealtimeConnectionState = "connecting" | "connected" | "disconnected" | "error";

export interface RealtimeInvalidation {
  event: "alert.invalidated";
  patient_id: string;
  alert_id?: number;
  audit_id?: number;
}
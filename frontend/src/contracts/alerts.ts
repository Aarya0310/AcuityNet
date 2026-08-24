import type { OperationalState } from "./realtime";

export type AlertState = "generated" | "assigned" | "acknowledged" | "responded" | "resolved";
export type AlertPriority = "high" | "critical";

export interface AlertEvent {
  event_id: number;
  sequence: number;
  state: AlertState;
  outcome: string;
  occurred_at: string;
}

export interface Alert {
  alert_id: number;
  patient_id: string;
  bed_id: string;
  priority: AlertPriority;
  state: AlertState;
  risk_score: number;
  risk_level: "low" | "moderate" | "high" | "critical";
  event: string;
  probability: number;
  horizon_minutes: number;
  observation_sequence: number;
  timestamp: string;
  provenance: { source_kind: string; source_name: string; scenario_id: string; scenario_version: string; is_live_bedside_feed: boolean };
  prototype_label: string;
  prediction_source_kind: "ml" | "deterministic_fallback";
  prediction_source_version: string;
  fallback_reason: string | null;
  prediction_contract_version: string;
  effective_threshold: number;
  rule_version: string;
  deduplication_status: "new_alert" | "reused_active" | "suppressed_cooldown" | "rearmed";
  created_at: string;
  assignment_id: string | null;
  events: AlertEvent[];
}

export interface AuditEvent {
  audit_id: number;
  sequence: number;
  actor_id: string | null;
  action: string;
  category: string;
  resource_type: string;
  resource_id: string;
  outcome: string;
  resulting_state: string | null;
  correlation_id: string;
  details: Record<string, unknown>;
  occurred_at: string;
}

export type AlertOperationalState = OperationalState | "deterministic_fallback";
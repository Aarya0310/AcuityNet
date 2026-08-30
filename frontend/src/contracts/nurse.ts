import type { Alert, AlertState } from "./alerts";
import type { FreshnessState } from "./vitals";

export type NurseLifecycleAction = "acknowledge" | "respond" | "resolve";

export interface NurseTimelineEntry {
  entry_id: string;
  entry_type: "alert" | "audit" | "annotation" | "fact" | "prediction";
  occurred_at: string;
  title: string;
  detail: string;
}

export interface NurseWorkResponse {
  patient_id: string;
  display_name: string;
  bed_id: string;
  unit: string;
  assignment_id: string;
  alert: Alert;
  vitals: {
    patient_id: string;
    patient: { patient_id: string; display_name: string; bed_id: string; unit: string };
    bed_id: string;
    unit: string;
    sequence: number;
    observed_at: string;
    received_at: string;
    spo2_percent: number;
    heart_rate_bpm: number;
    respiratory_rate_bpm: number;
    systolic_bp_mmhg: number;
    diastolic_bp_mmhg: number;
    temperature_c: number;
    provenance: {
      source_kind: string;
      source_name: string;
      scenario_id: string;
      scenario_version: string;
      is_live_bedside_feed: boolean;
    };
    freshness: FreshnessState;
    prototype_label: string;
  };
  diagnosis: string | null;
  prior_events: string[];
  timeline: NurseTimelineEntry[];
  allowed_actions: NurseLifecycleAction[];
}

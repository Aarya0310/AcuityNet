import type { PatientSummary } from "./patients";

export type FreshnessState = "fresh" | "stale" | "disconnected" | "unavailable";

export interface SyntheticProvenance {
  source_kind: "synthetic";
  source_name: "acuitynet-simulator";
  scenario_id: string;
  scenario_version: string;
  is_live_bedside_feed: false;
}

export interface VitalObservation {
  patient_id: string;
  patient: PatientSummary;
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
  provenance: SyntheticProvenance;
  freshness: FreshnessState;
  prototype_label: string;
}

import type { Alert } from "./alerts";
import type { Prediction } from "./predictions";

export type HistorianFactCategory = "diagnosis" | "medication" | "lab" | "icu_event";
export type ContextualStatus = "complete" | "incomplete";

export interface HistorianFact {
  fact_id: string;
  category: HistorianFactCategory;
  label: string;
  value: string | null;
  unit: string | null;
  effective_at: string;
  source_kind: "synthetic";
  source_name: string;
}

export interface RuleEvaluation {
  rule_key: string;
  rule_name: string;
  rule_version: string;
  category: HistorianFactCategory;
  fact_id: string;
  delta: number;
  explanation: string;
  evaluated_at: string;
}

export interface TimelineEntry {
  entry_id: string;
  entry_type: "fact" | "prediction" | "alert" | "audit" | "annotation";
  occurred_at: string;
  title: string;
  detail: string;
}

export interface Annotation {
  annotation_id: number;
  author_id: string;
  text: string;
  created_at: string;
  source_label: string;
}

export interface HistorianResponse {
  patient_id: string;
  patient_name: string;
  admission_id: string;
  admitted_at: string;
  bed_id: string;
  unit: string;
  current_prediction: Prediction & {
    timestamp: string;
    current_vitals: Record<string, unknown>;
    provenance: Record<string, unknown>;
    prototype_label: string;
    contract_version: string;
    source_kind: "ml" | "deterministic_fallback";
    source_version: string;
    fallback_reason: string | null;
  };
  baseline_score: number;
  contextual_status: ContextualStatus;
  contextual_score: number | null;
  facts: HistorianFact[];
  rule_evaluations: RuleEvaluation[];
  missing_evidence: string[];
  annotations: Annotation[];
  alert: Alert | null;
  timeline: TimelineEntry[];
  prototype_label: string;
  provenance: "synthetic" | "research-prototype";
}

export interface AnnotationCreate {
  text: string;
}

export interface DispatchCandidate {
  nurse_id: string;
  display_name: string;
  eligible: boolean;
  exclusion_reasons: string[];
  rank: number | null;
  score: number | null;
  components: Record<string, number>;
  contributions: Record<string, number>;
  proximity_km: number | null;
  workload_active: number | null;
  workload_capacity: number | null;
  acuity_compatibility: number | null;
  freshness: Record<string, string | null>;
}

export interface DispatchEvaluationResponse {
  evaluation_id: string;
  patient_id: string;
  alert_id: number;
  evidence_id: number;
  created_at: string;
  alert_fresh_at: string;
  candidate_fresh_at: string;
  status: "ready" | "blocked" | "no_eligible_candidate";
  recommendation_nurse_id: string | null;
  weights: Record<string, number>;
  candidates: DispatchCandidate[];
  exclusions: DispatchCandidate[];
  recommendation_context: string;
  prototype_label: string;
}

export interface DispatchDecisionRequest {
  evaluation_id: string;
  nurse_id: string;
  reason: string;
}

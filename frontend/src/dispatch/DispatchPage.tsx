import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import type { DispatchCandidate, DispatchEvaluationResponse } from "../contracts/dispatch";
import { getDispatchEvaluation, postDispatchConfirm, postDispatchOverride, postDispatchRetry } from "../api/client";

const weightLabels: Record<string, string> = {
  availability: "Availability",
  proximity: "Proximity",
  workload: "Workload",
  acuity_compatibility: "Acuity compatibility",
};

function formatScore(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }).format(new Date(value));
}

export function DispatchPage({ patientId = "P-1042" }: { patientId?: string }) {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [reason, setReason] = useState("");
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [selectedNurseId, setSelectedNurseId] = useState<string | null>(null);

  const evaluation = useQuery({
    queryKey: ["dispatch", patientId],
    queryFn: () => getDispatchEvaluation(patientId),
    retry: false,
  });

  const record = evaluation.data ?? null;

  const defaultOverrideNurseId = useMemo(() => {
    if (!record || !record.recommendation_nurse_id) return null;
    if (selectedNurseId && selectedNurseId !== record.recommendation_nurse_id) return selectedNurseId;
    const alternative = record.candidates.find((candidate) => candidate.nurse_id !== record.recommendation_nurse_id)?.nurse_id ?? record.recommendation_nurse_id;
    return alternative;
  }, [record, selectedNurseId]);

  const { recommended, alternatives } = useMemo(() => {
    if (!record) return { recommended: null, alternatives: [] as DispatchCandidate[] };
    const recommendedCandidate = record.candidates.find((candidate) => candidate.nurse_id === record.recommendation_nurse_id) ?? null;
    const alternativesList = record.candidates.filter((candidate) => candidate.nurse_id !== record.recommendation_nurse_id);
    return { recommended: recommendedCandidate, alternatives: alternativesList };
  }, [record]);

  const retryMutation = useMutation({
    mutationFn: () => postDispatchRetry(patientId),
    onSuccess: async (result) => {
      setDecisionError(null);
      setReason("");
      setSelectedNurseId(result.recommendation_nurse_id);
      await queryClient.invalidateQueries({ queryKey: ["dispatch", patientId] });
      await queryClient.refetchQueries({ queryKey: ["dispatch", patientId], type: "active" });
    },
    onError: () => setDecisionError("Dispatch evaluation could not be refreshed."),
  });

  const confirmMutation = useMutation({
    mutationFn: ({ nurseId, evaluationId }: { nurseId: string; evaluationId: string }) => postDispatchConfirm(patientId, { evaluation_id: evaluationId, nurse_id: nurseId, reason }),
    onSuccess: async () => {
      setDecisionError(null);
      setReason("");
      await queryClient.invalidateQueries({ queryKey: ["dispatch", patientId] });
      await queryClient.refetchQueries({ queryKey: ["dispatch", patientId], type: "active" });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error && error.message.includes("422") ? "A brief reason is required." : "Dispatch decision could not be recorded.";
      setDecisionError(message);
    },
  });

  const overrideMutation = useMutation({
    mutationFn: ({ nurseId, evaluationId }: { nurseId: string; evaluationId: string }) => postDispatchOverride(patientId, { evaluation_id: evaluationId, nurse_id: nurseId, reason }),
    onSuccess: async () => {
      setDecisionError(null);
      setReason("");
      await queryClient.invalidateQueries({ queryKey: ["dispatch", patientId] });
      await queryClient.refetchQueries({ queryKey: ["dispatch", patientId], type: "active" });
    },
    onError: () => setDecisionError("Override could not be recorded."),
  });

  if (evaluation.isLoading) return <main className="dispatch-shell"><p role="status">Loading dispatch review...</p></main>;
  if (evaluation.isError || !evaluation.data) {
    return <main className="dispatch-shell"><p role="alert">Dispatch evaluation unavailable. REST retry required.</p><button type="button" onClick={() => void retryMutation.mutateAsync()}>Retry evaluation</button></main>;
  }

  const submitDecision = (event: FormEvent<HTMLFormElement>, action: "confirm" | "override") => {
    event.preventDefault();
    const trimmedReason = reason.trim();
    if (!trimmedReason) {
      setDecisionError("A brief reason is required.");
      return;
    }
    setDecisionError(null);
    const confirmNurseId = record.recommendation_nurse_id ?? "";
    const overrideNurseId = defaultOverrideNurseId ?? selectedNurseId ?? record.recommendation_nurse_id ?? "";
    if (!confirmNurseId && action === "confirm") return;
    if (!overrideNurseId && action === "override") return;
    if (action === "confirm") {
      void confirmMutation.mutateAsync({ nurseId: confirmNurseId, evaluationId: record.evaluation_id });
      return;
    }
    void overrideMutation.mutateAsync({ nurseId: overrideNurseId, evaluationId: record.evaluation_id });
  };

  const decisionDisabled = record.status !== "ready" || !record.recommendation_nurse_id;

  return (
    <main className="dispatch-shell">
      <header className="dispatch-header">
        <div>
          <p className="eyebrow">AcuityNet / Dispatch review</p>
          <h2>Dispatch review</h2>
        </div>
        <div className="dispatch-status" role="status">
          <strong>{record.status === "ready" ? "Recommended" : record.status === "blocked" ? "Blocked by stale evidence" : "No eligible nurse"}</strong>
          <span>{record.recommendation_context}</span>
        </div>
      </header>

      <section className="prototype-banner" aria-label="Prototype label">{record.prototype_label}</section>

      {record.status === "ready" && recommended ? (
        <section className="dispatch-recommendation" aria-label="Recommended candidate">
          <div>
            <p className="eyebrow">Recommended nurse</p>
            <h3>{recommended.display_name}</h3>
            <p>{recommended.nurse_id}</p>
          </div>
          <div>
            <strong>{formatScore(recommended.score)}</strong>
            <span>Overall score</span>
          </div>
        </section>
      ) : (
        <section className="dispatch-blocked" role="alert">
          <h3>No eligible nurse</h3>
          <p>Alert remains generated and unassigned</p>
          <ul>{record.exclusions.map((candidate) => <li key={candidate.nurse_id}>{candidate.display_name}: {candidate.exclusion_reasons.join(", ") || "Eligibility unavailable"}</li>)}</ul>
          <button type="button" onClick={() => void retryMutation.mutateAsync()} disabled={retryMutation.isPending}>Retry evaluation</button>
        </section>
      )}

      <section className="dispatch-weights" aria-label="Weighted scoring breakdown">
        <h3>Ranking evidence</h3>
        <div className="dispatch-weight-grid">
          {Object.entries(record.weights).map(([key, value]) => (
            <div key={key} className="dispatch-weight-item">
              <span>{weightLabels[key] ?? key}</span>
              <strong>{value * 100}%</strong>
              <small>{value * 100}% weight</small>
            </div>
          ))}
        </div>
      </section>

      <section className="dispatch-candidates" aria-label="Candidate comparison">
        <h3>Candidate comparison</h3>
        <div className="dispatch-candidate-list">
          {(record.status === "ready" ? [recommended, ...alternatives].filter(Boolean) : record.exclusions).map((candidate) => {
            const item = candidate as DispatchCandidate;
            const isSelected = selectedNurseId === item.nurse_id;
            return (
              <article key={item.nurse_id} className={`dispatch-candidate ${isSelected ? "selected" : ""}`}>
                <div className="candidate-header">
                  <div>
                    <strong>{item.display_name}</strong>
                    <small>{item.nurse_id}</small>
                  </div>
                  <div className="candidate-score">
                    <span>Rank {item.rank ?? "—"}</span>
                    <strong>{formatScore(item.score)}</strong>
                  </div>
                </div>
                <div className="candidate-components">
                  {Object.entries(item.components).length ? Object.entries(item.components).map(([key, componentValue]) => (
                    <div key={key}>
                      <span>{weightLabels[key] ?? key}</span>
                      <strong>{componentValue.toFixed(2)}</strong>
                    </div>
                  )) : <div><span>Eligibility</span><strong>{item.exclusion_reasons.join(", ") || "Requires review"}</strong></div>}
                </div>
                <div className="candidate-meta">
                  <span>Distance: {item.proximity_km ?? "—"} km</span>
                  <span>Workload: {item.workload_active ?? "—"}/{item.workload_capacity ?? "—"}</span>
                  <span>Freshness: {Object.values(item.freshness).some(Boolean) ? Object.entries(item.freshness).map(([key, value]) => `${key}: ${formatTimestamp(value)}`).join(" • ") : "No freshness data"}</span>
                </div>
                <div className="candidate-exclusions">
                  {item.exclusion_reasons.length ? item.exclusion_reasons.map((reason) => <span key={reason}>{reason}</span>) : <span>Eligibility clear</span>}
                </div>
                <button type="button" onClick={() => setSelectedNurseId(item.nurse_id)} disabled={record.status !== "ready" && item.eligible === false}>
                  {item.nurse_id === record.recommendation_nurse_id ? "Select recommendation" : `Choose ${item.display_name}`}
                </button>
              </article>
            );
          })}
        </div>
      </section>

      {record.exclusions.length > 0 ? (
        <section className="dispatch-exclusions" aria-label="Excluded candidates">
          <h3>Excluded candidates</h3>
          <ul>
            {record.exclusions.map((candidate) => (
              <li key={candidate.nurse_id}><strong>{candidate.display_name}</strong>: {candidate.exclusion_reasons.join(", ") || "Eligibility unavailable"}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {user && (user.role === "admin" || user.role === "doctor") && record.status === "ready" ? (
        <form className="dispatch-decision" onSubmit={(event) => submitDecision(event, "confirm")}>
          <h3>Decision</h3>
          <label htmlFor="dispatch-reason">Decision reason</label>
          <textarea id="dispatch-reason" aria-label="Decision reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={3} maxLength={240} />
          <div className="decision-actions">
            <button type="submit" disabled={decisionDisabled} aria-label="Confirm recommendation">Confirm recommendation</button>
            <button type="button" onClick={(event) => { event.preventDefault(); void overrideMutation.mutateAsync({ nurseId: defaultOverrideNurseId ?? record.recommendation_nurse_id ?? "", evaluationId: record.evaluation_id }); }} disabled={decisionDisabled} aria-label={`Override with ${defaultOverrideNurseId ? (record.candidates.find((candidate) => candidate.nurse_id === defaultOverrideNurseId)?.display_name ?? defaultOverrideNurseId) : "selected nurse"}`}>
              {defaultOverrideNurseId ? `Override with ${record.candidates.find((candidate) => candidate.nurse_id === defaultOverrideNurseId)?.display_name ?? defaultOverrideNurseId}` : "Override recommendation"}
            </button>
          </div>
          {decisionError ? <p role="alert">{decisionError}</p> : null}
          {confirmMutation.isSuccess || overrideMutation.isSuccess ? <p role="status">Dispatch decision recorded</p> : null}
        </form>
      ) : null}
    </main>
  );
}

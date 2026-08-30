import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { getNurseWork, postNurseLifecycleAction } from "../api/client";
import type { NurseLifecycleAction, NurseWorkResponse } from "../contracts/nurse";

export function NurseWorkPage({ patientId = "P-1042" }: { patientId?: string }) {
  const queryClient = useQueryClient();
  const nurseWork = useQuery({ queryKey: ["nurse-work", patientId], queryFn: () => getNurseWork(patientId), retry: false });
  const [action, setAction] = useState<NurseLifecycleAction | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!action) return;
    const value = note.trim();
    if ((action === "respond" || action === "resolve") && !value) {
      setError("Note required");
      return;
    }
    setError(null);
    await postNurseLifecycleAction(patientId, action, action === "acknowledge" ? undefined : value);
    setNote("");
    setAction(null);
    await queryClient.invalidateQueries({ queryKey: ["nurse-work", patientId] });
  }

  if (nurseWork.isLoading) {
    return <main className="nurse-shell"><p role="status">Loading assigned work...</p></main>;
  }
  if (nurseWork.isError || !nurseWork.data) {
    return <main className="nurse-shell"><p role="alert">Assigned work unavailable. REST retry required.</p><button type="button" onClick={() => void nurseWork.refetch()}>Retry</button></main>;
  }

  const work = nurseWork.data as NurseWorkResponse;
  const nextAction = action ?? work.allowed_actions[0] ?? null;

  return (
    <main className="nurse-shell">
      <header className="nurse-header">
        <div>
          <p className="eyebrow">AcuityNet / Nursing workflow</p>
          <h1>Assigned work</h1>
        </div>
        <div className="nurse-state" role="status">
          <strong>{work.alert.state}</strong>
          <span>Assignment {work.assignment_id}</span>
        </div>
      </header>

      <section className="nurse-patient" aria-label="Assigned patient">
        <h2>{work.display_name}</h2>
        <p>Patient {work.patient_id} / {work.bed_id} / {work.unit}</p>
      </section>

      <section className="nurse-alert" aria-label="Patient alert">
        <h3>Alert</h3>
        <p><strong>{work.alert.priority}</strong> priority / {work.alert.event}</p>
        <p>Risk {work.alert.risk_score.toFixed(2)} / {work.alert.risk_level}</p>
        <p>Lifecycle: {work.alert.state}</p>
      </section>

      <section className="nurse-vitals" aria-label="Latest vitals">
        <h3>Latest vitals</h3>
        <p>SpO2 {work.vitals.spo2_percent}% / Heart rate {work.vitals.heart_rate_bpm} bpm</p>
        <p>Resp {work.vitals.respiratory_rate_bpm}/min / BP {work.vitals.systolic_bp_mmhg}/{work.vitals.diastolic_bp_mmhg} mmHg</p>
        <p>Temp {work.vitals.temperature_c} C</p>
      </section>

      <section className="nurse-context" aria-label="Assigned patient context">
        <h3>Context</h3>
        {work.diagnosis ? <p>{work.diagnosis}</p> : <p>No diagnosis available.</p>}
        {work.prior_events.length ? <ul>{work.prior_events.map((event) => <li key={event}>{event}</li>)}</ul> : <p>No prior events.</p>}
      </section>

      <section className="nurse-actions" aria-label="Allowed actions">
        <h3>Action</h3>
        {work.allowed_actions.length ? (
          <form onSubmit={(event) => void submit(event)}>
            {work.allowed_actions.map((item) => (
              <button key={item} type="button" onClick={() => setAction(item)} aria-pressed={nextAction === item}>{item}</button>
            ))}
            {nextAction && (nextAction === "respond" || nextAction === "resolve") ? (
              <div>
                <label htmlFor="nurse-note">{nextAction === "respond" ? "Response note" : "Resolution note"}</label>
                <textarea id="nurse-note" value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add a concise note..." />
              </div>
            ) : null}
            {nextAction ? <button type="submit">{nextAction}</button> : null}
            {error ? <p role="alert">{error}</p> : null}
          </form>
        ) : (
          <p>No actions remaining.</p>
        )}
      </section>

      <section className="nurse-timeline" aria-label="Nurse timeline">
        <h3>Timeline</h3>
        <ul>
          {work.timeline.map((entry) => (
            <li key={entry.entry_id}>
              <strong>{entry.title}</strong>
              <p>{entry.detail}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

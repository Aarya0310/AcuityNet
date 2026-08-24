import type { FreshnessState, VitalObservation } from "../contracts/vitals";

const PROTOTYPE_LABEL = "Simulated ICU environment - research prototype - not for clinical use";

const stateCopy: Record<FreshnessState, { label: string; detail: string }> = {
  fresh: { label: "Feed current", detail: "Server reports a recent synthetic observation." },
  stale: { label: "Feed stale", detail: "The server reports that this synthetic observation is older than the fresh window." },
  disconnected: { label: "Feed disconnected", detail: "The server reports that the synthetic feed is not currently connected." },
  unavailable: { label: "Feed unavailable", detail: "No synthetic observation is available from the server." },
};

interface MonitoringPageProps {
  observation?: VitalObservation;
  freshnessOverride?: FreshnessState;
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "medium", timeZone: "UTC" }).format(new Date(value));
}

export function MonitoringPage({ observation, freshnessOverride }: MonitoringPageProps) {
  const freshness = freshnessOverride ?? observation?.freshness ?? "unavailable";
  const state = stateCopy[freshness];

  return (
    <main className="monitoring-shell">
      <header className="monitoring-header">
        <div>
          <p className="eyebrow">AcuityNet / Monitoring</p>
          <h1>{observation?.patient.display_name ?? "P-1042"}</h1>
          <p className="patient-id">Patient {observation?.patient_id ?? "P-1042"}</p>
        </div>
        <div className={`status status-${freshness}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          <strong>{state.label}</strong>
          <span>{state.detail}</span>
        </div>
      </header>

      <div className="prototype-banner" role="note">{PROTOTYPE_LABEL}</div>

      {observation ? (
        <>
          <section className="context-strip" aria-label="Patient context">
            <div><span>Bed</span><strong>{observation.bed_id}</strong></div>
            <div><span>Unit</span><strong>{observation.unit}</strong></div>
            <div><span>Observation</span><strong>{formatTimestamp(observation.observed_at)} UTC</strong></div>
            <div><span>Received</span><strong>{formatTimestamp(observation.received_at)} UTC</strong></div>
          </section>

          <section className="vitals-grid" aria-label="Current synthetic vitals">
            <VitalCard label="SpO2" value={`${observation.spo2_percent} %`} />
            <VitalCard label="Heart rate" value={`${observation.heart_rate_bpm} bpm`} />
            <VitalCard label="Respiratory rate" value={`${observation.respiratory_rate_bpm} /min`} />
            <VitalCard label="Systolic BP" value={`${observation.systolic_bp_mmhg} mmHg`} />
            <VitalCard label="Diastolic BP" value={`${observation.diastolic_bp_mmhg} mmHg`} />
            <VitalCard label="Temperature" value={`${observation.temperature_c} C`} />
          </section>

          <footer className="provenance">
            <span>Sequence: {observation.sequence}</span>
            <span>Source: {observation.provenance.source_name}</span>
            <span>Scenario: {observation.provenance.scenario_id} v{observation.provenance.scenario_version}</span>
            <span>Live bedside feed: {observation.provenance.is_live_bedside_feed ? "yes" : "no"}</span>
            <span>Server label: {observation.prototype_label}</span>
          </footer>
        </>
      ) : (
        <section className="empty-state" aria-label="Unavailable observation">
          <h2>No current synthetic observation</h2>
          <p>{state.detail}</p>
        </section>
      )}
    </main>
  );
}

function VitalCard({ label, value }: { label: string; value: string }) {
  return <article className="vital-card"><span>{label}</span><strong>{value}</strong></article>;
}

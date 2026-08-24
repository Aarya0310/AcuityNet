import { useEffect, useRef, useState } from "react";
import type { FreshnessState, VitalObservation } from "../contracts/vitals";
import type { AutomaticRefreshInterval, RefreshConfiguration, RefreshInterval } from "../contracts/configuration";
import { advanceVitals, getCurrentVitals, getRefreshConfiguration } from "../api/client";
import { ProvenanceBadge } from "../safety/ProvenanceBadge";
import { PrototypeBanner } from "../safety/PrototypeBanner";

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
  const [currentObservation, setCurrentObservation] = useState(observation);
  const [configuration, setConfiguration] = useState<RefreshConfiguration>();
  const [selectedInterval, setSelectedInterval] = useState<RefreshInterval>();
  const refreshInFlight = useRef(false);
  const patientId = observation?.patient_id ?? "P-1042";

  useEffect(() => setCurrentObservation(observation), [observation]);

  useEffect(() => {
    let active = true;
    getRefreshConfiguration().then((value) => {
      if (active) {
        setConfiguration(value);
        setSelectedInterval(value.default_interval);
      }
    }).catch(() => {
      if (active) setSelectedInterval("manual");
    });
    return () => { active = false; };
  }, []);

  const refresh = async (interval: AutomaticRefreshInterval) => {
    if (refreshInFlight.current) return;
    refreshInFlight.current = true;
    try {
      await advanceVitals(patientId, interval);
      setCurrentObservation(await getCurrentVitals(patientId));
    } finally {
      refreshInFlight.current = false;
    }
  };

  useEffect(() => {
    if (!selectedInterval || selectedInterval === "manual") return;
    const timer = window.setInterval(() => { void refresh(selectedInterval); }, selectedInterval * 1000);
    return () => window.clearInterval(timer);
  }, [selectedInterval, patientId]);

  const displayedObservation = currentObservation;
  const freshness = freshnessOverride ?? displayedObservation?.freshness ?? "unavailable";
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

      <PrototypeBanner />

      <section className="refresh-controls" aria-label="Refresh controls">
        <label htmlFor="refresh-interval">Refresh interval</label>
        <select
          id="refresh-interval"
          aria-label="Refresh interval"
          value={selectedInterval ?? ""}
          disabled={!configuration}
          onChange={(event) => setSelectedInterval(event.target.value === "manual" ? "manual" : Number(event.target.value) as AutomaticRefreshInterval)}
        >
          {(configuration?.supported_intervals ?? []).map((interval) => (
            <option key={interval} value={interval}>
              {interval === "manual" ? "Manual" : `${interval} seconds`}
            </option>
          ))}
        </select>
        <button type="button" onClick={() => void refresh(selectedInterval === "manual" ? configuration?.default_interval ?? 10 : selectedInterval ?? 10)}>
          Refresh now
        </button>
      </section>

      {displayedObservation ? (
        <>
          <section className="context-strip" aria-label="Patient context">
            <div><span>Bed</span><strong>{displayedObservation.bed_id}</strong></div>
            <div><span>Unit</span><strong>{displayedObservation.unit}</strong></div>
            <div><span>Observation</span><strong>{formatTimestamp(displayedObservation.observed_at)} UTC</strong></div>
            <div><span>Received</span><strong>{formatTimestamp(displayedObservation.received_at)} UTC</strong></div>
          </section>

          <section className="vitals-grid" aria-label="Current synthetic vitals">
            <VitalCard label="SpO2" value={`${displayedObservation.spo2_percent} %`} />
            <VitalCard label="Heart rate" value={`${displayedObservation.heart_rate_bpm} bpm`} />
            <VitalCard label="Respiratory rate" value={`${displayedObservation.respiratory_rate_bpm} /min`} />
            <VitalCard label="Systolic BP" value={`${displayedObservation.systolic_bp_mmhg} mmHg`} />
            <VitalCard label="Diastolic BP" value={`${displayedObservation.diastolic_bp_mmhg} mmHg`} />
            <VitalCard label="Temperature" value={`${displayedObservation.temperature_c} C`} />
          </section>

          <ProvenanceBadge sequence={displayedObservation.sequence} provenance={displayedObservation.provenance} prototypeLabel={displayedObservation.prototype_label} />
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

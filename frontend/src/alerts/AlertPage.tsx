import { useQuery } from "@tanstack/react-query";
import { getAlertAudit, getAlertEvents, getCurrentAlert } from "../api/client";
import type { Alert, AlertOperationalState } from "../contracts/alerts";
import { OperationalState } from "../operational/OperationalState";
import { PrototypeBanner } from "../safety/PrototypeBanner";
import { useAlertRealtime } from "./useAlertRealtime";

export function AlertPage({ patientId = "P-1042", operationalState }: { patientId?: string; operationalState?: AlertOperationalState }) {
  const alert = useQuery({ queryKey: ["alert", patientId], queryFn: () => getCurrentAlert(patientId), retry: false });
  const events = useQuery({ queryKey: ["alert-events", patientId], queryFn: () => getAlertEvents(patientId), retry: false, enabled: Boolean(alert.data) });
  const audit = useQuery({ queryKey: ["alert-audit", patientId], queryFn: () => getAlertAudit(patientId), retry: false });
  const realtime = useAlertRealtime(patientId);
  const hasData = Boolean(alert.data);
  let state: AlertOperationalState = operationalState ?? "loading";
  if (!operationalState) {
    if (!alert.isLoading && alert.isError) state = hasData ? "stale" : "unavailable_fallback";
    else if (!alert.isLoading && !alert.data) state = "no_active_alert";
    else if (!alert.isLoading && alert.data?.prediction_source_kind === "deterministic_fallback") state = "deterministic_fallback";
    else if (realtime.state === "disconnected" || realtime.state === "error") state = hasData ? "disconnected" : "unavailable_fallback";
  }

  return (
    <main className="alert-shell">
      <header className="alert-header"><div><p className="eyebrow">AcuityNet / Alert evidence</p><h2>Patient {patientId}</h2></div><span className="connection-state">Realtime: {realtime.state}</span></header>
      <PrototypeBanner />
      <OperationalState state={state} connection={realtime.state} retry={() => { void alert.refetch(); void audit.refetch(); }} />
      {alert.data ? <AlertEvidence alert={alert.data} eventCount={events.data?.length ?? alert.data.events.length} auditCount={audit.data?.length ?? 0} /> : null}
      {audit.isError ? <p role="alert">Audit evidence unavailable. REST retry required.</p> : null}
    </main>
  );
}

function AlertEvidence({ alert, eventCount, auditCount }: { alert: Alert; eventCount: number; auditCount: number }) {
  return <section className="alert-evidence"><div className="alert-summary"><span>{alert.priority} priority</span><strong>{alert.event}</strong><span>Risk {alert.risk_score.toFixed(2)} / {alert.risk_level}</span><span>Lifecycle: {alert.state}</span></div><dl><div><dt>Source</dt><dd>{alert.prediction_source_kind} / {alert.prediction_source_version}</dd></div><div><dt>Fallback reason</dt><dd>{alert.fallback_reason ?? "None reported"}</dd></div><div><dt>Provenance</dt><dd>{alert.provenance.source_name}, {alert.provenance.scenario_id} v{alert.provenance.scenario_version}</dd></div><div><dt>Evidence</dt><dd>{eventCount} lifecycle events, {auditCount} audit entries</dd></div></dl><p className="prototype-note">{alert.prototype_label}</p></section>;
}
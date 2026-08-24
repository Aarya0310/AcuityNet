import type { ReactNode } from "react";
import type { AlertOperationalState } from "../contracts/alerts";
import type { RealtimeConnectionState } from "../contracts/realtime";

const copy: Record<AlertOperationalState, { label: string; detail: string }> = {
  loading: { label: "Loading authoritative state", detail: "Reading alert evidence from REST." },
  stale: { label: "Alert evidence stale", detail: "The last successful value is retained, but it is not current." },
  disconnected: { label: "Realtime disconnected", detail: "REST remains authoritative. Reconnect is in progress or unavailable." },
  unavailable_fallback: { label: "Alert unavailable", detail: "The server could not provide current alert evidence." },
  no_active_alert: { label: "No active alert", detail: "REST reports no unresolved alert for this patient." },
  no_candidate: { label: "No candidate available", detail: "Candidate evaluation is not provided in this prototype." },
  not_yet_available: { label: "Not yet available", detail: "This evidence has not been supplied by the server." },
  deterministic_fallback: { label: "Deterministic fallback", detail: "This result uses the server's deterministic fallback and is not a validated clinical model." },
};

export function OperationalState({ state, connection, retry, children }: { state: AlertOperationalState; connection?: RealtimeConnectionState; retry?: () => void; children?: ReactNode }) {
  const status = connection ? `${copy[state].label} / realtime ${connection}` : copy[state].label;
  return (
    <section className={`operational-state operational-${state}`} role="status" aria-label={status}>
      <strong>{copy[state].label}</strong>
      <span>{copy[state].detail}</span>
      {retry ? <button type="button" onClick={retry}>Retry REST</button> : null}
      {children}
    </section>
  );
}
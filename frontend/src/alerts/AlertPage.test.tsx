import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AlertPage } from "./AlertPage";

const alert = {
  alert_id: 1, patient_id: "P-1042", bed_id: "ICU-12", priority: "critical", state: "generated", risk_score: 0.91, risk_level: "critical", event: "Deterioration", probability: 0.91, horizon_minutes: 30, observation_sequence: 3, timestamp: "2026-08-24T10:00:00Z",
  provenance: { source_kind: "synthetic", source_name: "acuitynet-simulator", scenario_id: "p1042-deterioration", scenario_version: "1", is_live_bedside_feed: false }, prototype_label: "Research prototype: simulated ICU data, not clinical advice.", prediction_source_kind: "deterministic_fallback", prediction_source_version: "rules-v1", fallback_reason: "Model unavailable", prediction_contract_version: "1", effective_threshold: 0.8, rule_version: "rules-v1", deduplication_status: "new_alert", created_at: "2026-08-24T10:00:00Z", assignment_id: null, events: [],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><AlertPage /></QueryClientProvider>);
}

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("AlertPage", () => {
  it("reads alert, events, and audit from REST and shows fallback provenance", async () => {
    vi.stubGlobal("localStorage", { getItem: () => "token" });
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.endsWith("/alert")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(alert) });
      if (url.endsWith("/alert/events")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ events: [] }) });
    }));
    vi.stubGlobal("WebSocket", class { onopen = null; onmessage = null; onerror = null; onclose = null; close() {} });
    renderPage();
    expect(await screen.findByText("Deterioration")).toBeInTheDocument();
    expect(screen.getByText("Deterministic fallback")).toBeInTheDocument();
    expect(screen.getByText(/acuitynet-simulator/)).toBeInTheDocument();
    expect(screen.getByText(/Realtime: connecting|Realtime: disconnected/)).toBeInTheDocument();
  });

  it("shows an explicit unavailable state when the authoritative alert request fails", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 503, json: () => Promise.resolve({}) })));
    vi.stubGlobal("WebSocket", class { close() {} });
    renderPage();
    expect(await screen.findByText("Alert unavailable")).toBeInTheDocument();
    expect(screen.getByText(/could not provide current alert evidence/i)).toBeInTheDocument();
  });

  it("reports no active alert from a successful REST empty response", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(url.endsWith("/audit") ? { events: [] } : null) })));
    vi.stubGlobal("WebSocket", class { close() {} });
    renderPage();
    expect(await screen.findByText("No active alert")).toBeInTheDocument();
  });
});
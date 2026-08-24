import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
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

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  constructor(readonly url: string) { FakeWebSocket.instances.push(this); }
  open() { this.onopen?.(); }
  message(value: unknown) { this.onmessage?.({ data: JSON.stringify(value) } as MessageEvent); }
  error() { this.onerror?.(); }
  close() { this.onclose?.(); }
}

afterEach(() => { cleanup(); FakeWebSocket.instances = []; vi.useRealTimers(); vi.unstubAllGlobals(); localStorage.removeItem("acuitynet.access_token"); });

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

  it("shows loading before the authoritative REST response arrives", () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(null) })));
    vi.stubGlobal("WebSocket", class { close() {} });
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><AlertPage operationalState="loading" /></QueryClientProvider>);
    expect(screen.getByRole("status", { name: /loading authoritative state/i })).toBeInTheDocument();
  });

  it("retains the last REST value but marks it stale after a failed refresh", async () => {
    let alertRequestCount = 0;
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.endsWith("/alert")) {
        alertRequestCount += 1;
        return alertRequestCount === 1
          ? Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(alert) })
          : Promise.reject(new Error("network failure"));
      }
      if (url.endsWith("/alert/events")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ events: [] }) });
    }));
    vi.stubGlobal("WebSocket", class { close() {} });
    renderPage();
    expect(await screen.findByText("Deterioration")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry REST" }));
    expect(await screen.findByText("Alert evidence stale")).toBeInTheDocument();
    expect(screen.getByText("Deterioration")).toBeInTheDocument();
  });

  it.each([401, 403])("shows unavailable state for REST authorization failure %s", async (status) => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status, json: () => Promise.resolve({}) })));
    vi.stubGlobal("WebSocket", class { close() {} });
    renderPage();
    expect(await screen.findByText("Alert unavailable")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry REST" })).toBeInTheDocument();
  });

  it.each([
    ["no_candidate", "No candidate available"],
    ["not_yet_available", "Not yet available"],
  ] as const)("renders typed %s without fabricating evidence", (state, label) => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(null) })));
    vi.stubGlobal("WebSocket", class { close() {} });
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><AlertPage operationalState={state} /></QueryClientProvider>);
    expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.queryByText(/candidate assignment|diagnos|validated weights/i)).not.toBeInTheDocument();
  });

  it("validates socket scope, recovers through REST, bounds reconnect, and cleans up", async () => {
    vi.useFakeTimers();
    localStorage.setItem("acuitynet.access_token", "token");
    const fetchMock = vi.fn((url: string) => {
      if (url.endsWith("/alert")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(alert) });
      if (url.endsWith("/alert/events")) return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ events: [] }) });
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("WebSocket", FakeWebSocket);
    renderPage();
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    const socket = FakeWebSocket.instances[0];
    expect(socket.url).toContain("access_token=token");
    act(() => socket.open());
    expect(screen.getByText("Realtime: connected")).toBeInTheDocument();
    const initialFetches = fetchMock.mock.calls.length;
    act(() => socket.message({ event: "alert.invalidated", patient_id: "P-other" }));
    act(() => socket.message({ event: "not-an-invalidation", patient_id: "P-1042" }));
    expect(fetchMock).toHaveBeenCalledTimes(initialFetches);
    act(() => socket.message({ event: "alert.invalidated", patient_id: "P-1042", alert_id: 1 }));
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    expect(fetchMock.mock.calls.length).toBeGreaterThan(initialFetches);

    act(() => socket.error());
    expect(screen.getByText("Realtime: error")).toBeInTheDocument();
    act(() => socket.close());
    expect(screen.getByText("Realtime: disconnected")).toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(FakeWebSocket.instances).toHaveLength(2);

    cleanup();
    await act(async () => { await vi.advanceTimersByTimeAsync(32000); });
    expect(FakeWebSocket.instances).toHaveLength(2);
  });
});
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthContext } from "../auth/AuthContext";
import { NurseWorkPage } from "./NurseWorkPage";

const nurseWork = {
  patient_id: "P-1042",
  display_name: "Fictional Patient 1042",
  bed_id: "ICU-12",
  unit: "ICU",
  assignment_id: "N-SARAH",
  alert: {
    alert_id: 42,
    patient_id: "P-1042",
    bed_id: "ICU-12",
    priority: "critical",
    state: "assigned",
    risk_score: 0.91,
    risk_level: "critical",
    event: "Deterioration",
    probability: 0.91,
    horizon_minutes: 30,
    observation_sequence: 3,
    timestamp: "2026-08-24T10:00:00Z",
    provenance: { source_kind: "synthetic", source_name: "acuitynet-simulator", scenario_id: "p1042-deterioration", scenario_version: "1", is_live_bedside_feed: false },
    prototype_label: "Research prototype: simulated ICU data, not clinical advice.",
    prediction_source_kind: "deterministic_fallback",
    prediction_source_version: "rules-v1",
    fallback_reason: "Model unavailable",
    prediction_contract_version: "1",
    effective_threshold: 0.8,
    rule_version: "rules-v1",
    deduplication_status: "new_alert",
    created_at: "2026-08-24T10:00:00Z",
    assignment_id: "N-SARAH",
    events: [],
  },
  vitals: {
    patient_id: "P-1042",
    patient: { patient_id: "P-1042", display_name: "Fictional Patient 1042", bed_id: "ICU-12", unit: "ICU" },
    bed_id: "ICU-12",
    unit: "ICU",
    sequence: 3,
    observed_at: "2026-08-24T10:00:00Z",
    received_at: "2026-08-24T10:00:00Z",
    spo2_percent: 92,
    heart_rate_bpm: 110,
    respiratory_rate_bpm: 28,
    systolic_bp_mmhg: 92,
    diastolic_bp_mmhg: 56,
    temperature_c: 38.4,
    provenance: { source_kind: "synthetic", source_name: "acuitynet-simulator", scenario_id: "p1042-deterioration", scenario_version: "1", is_live_bedside_feed: false },
    freshness: "fresh",
    prototype_label: "Research prototype: simulated ICU data, not clinical advice.",
  },
  diagnosis: "fictional chronic respiratory condition",
  prior_events: ["fictional prior respiratory observation"],
  timeline: [
    { entry_id: "audit:1", entry_type: "audit", occurred_at: "2026-08-24T10:00:00Z", title: "lifecycle.assign", detail: "assigned to Sarah" },
    { entry_id: "alert:42", entry_type: "alert", occurred_at: "2026-08-24T10:00:00Z", title: "Alert generated", detail: "critical" },
  ],
  allowed_actions: ["acknowledge"],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <AuthContext.Provider value={{ user: { user_id: "U-SARAH", username: "sarah", display_name: "Sarah Morgan", role: "nurse" }, loading: false, error: null, signIn: vi.fn(), signOut: vi.fn() }}>
      <QueryClientProvider client={client}><NurseWorkPage patientId="P-1042" /></QueryClientProvider>
    </AuthContext.Provider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("NurseWorkPage", () => {
  it("shows assigned work and only the allowed action for the nurse", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.includes("/nurse/work")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(nurseWork) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ state: "acknowledged", assignment_id: "N-SARAH" }) });
    }));

    renderPage();
    expect(await screen.findByText(/assigned work/i)).toBeInTheDocument();
    expect(screen.getByText("Fictional Patient 1042")).toBeInTheDocument();
    expect(screen.getByText(/acknowledge/i)).toBeInTheDocument();
    expect(screen.getByText(/fictional chronic respiratory condition/i)).toBeInTheDocument();
  });

  it("requires a note for respond and resolve actions and keeps the timeline on screen", async () => {
    let calls: { action?: string; note?: string }[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.includes("/nurse/work")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ...nurseWork, allowed_actions: ["respond"], alert: { ...nurseWork.alert, state: "acknowledged" } }) });
      }
      calls.push({ action: init && JSON.parse(String(init.body)).action, note: JSON.parse(String(init?.body ?? '{}')).note });
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ state: "responded", assignment_id: "N-SARAH" }) });
    }));

    renderPage();
    expect(await screen.findByText(/response note/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /respond/i }));
    expect(screen.getByText(/note required/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/response note/i), { target: { value: "Patient stabilized and reviewed." } });
    fireEvent.click(screen.getByRole("button", { name: /respond/i }));
    await waitFor(() => expect(calls.some((call) => call.action === "respond")).toBe(true));
    expect(screen.getByText(/timeline/i)).toBeInTheDocument();
  });
});

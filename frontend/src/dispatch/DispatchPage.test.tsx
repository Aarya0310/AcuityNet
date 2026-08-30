import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, cleanup } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { AuthContext } from "../auth/AuthContext";
import { DispatchPage } from "./DispatchPage";

const evaluation = {
  evaluation_id: "DPE-123",
  patient_id: "P-1042",
  alert_id: 1,
  evidence_id: 10,
  created_at: "2026-08-24T10:00:00Z",
  alert_fresh_at: "2026-08-24T10:00:00Z",
  candidate_fresh_at: "2026-08-24T10:00:00Z",
  status: "ready",
  recommendation_nurse_id: "N-SARAH",
  recommendation_context: "Ranked synthetic prototype recommendation; human confirmation required.",
  prototype_label: "Simulated ICU environment - research prototype - not for clinical use",
  weights: { availability: 0.4, proximity: 0.3, workload: 0.2, acuity_compatibility: 0.1 },
  candidates: [
    {
      nurse_id: "N-SARAH",
      display_name: "Sarah Lee",
      eligible: true,
      exclusion_reasons: [],
      rank: 1,
      score: 0.93,
      components: { availability: 1, proximity: 0.9, workload: 0.75, acuity_compatibility: 1 },
      contributions: { availability: 0.4, proximity: 0.27, workload: 0.15, acuity_compatibility: 0.1 },
      proximity_km: 2.1,
      workload_active: 2,
      workload_capacity: 8,
      acuity_compatibility: 1,
      freshness: { status: "2026-08-24T09:55:00Z", workload: "2026-08-24T09:55:00Z", proximity: "2026-08-24T09:55:00Z", acuity: "2026-08-24T09:55:00Z" },
    },
    {
      nurse_id: "N-REED",
      display_name: "Reed Clay",
      eligible: true,
      exclusion_reasons: [],
      rank: 2,
      score: 0.82,
      components: { availability: 1, proximity: 0.75, workload: 0.65, acuity_compatibility: 0.7 },
      contributions: { availability: 0.4, proximity: 0.225, workload: 0.13, acuity_compatibility: 0.07 },
      proximity_km: 4.4,
      workload_active: 3,
      workload_capacity: 8,
      acuity_compatibility: 0.7,
      freshness: { status: "2026-08-24T09:54:00Z", workload: "2026-08-24T09:54:00Z", proximity: "2026-08-24T09:54:00Z", acuity: "2026-08-24T09:54:00Z" },
    },
  ],
  exclusions: [
    {
      nurse_id: "N-BOYD",
      display_name: "Boyd Hall",
      eligible: false,
      exclusion_reasons: ["stale status", "unavailable"],
      rank: null,
      score: null,
      components: {},
      contributions: {},
      proximity_km: null,
      workload_active: null,
      workload_capacity: null,
      acuity_compatibility: null,
      freshness: { status: "2026-08-24T09:45:00Z", workload: "2026-08-24T09:45:00Z", proximity: "2026-08-24T09:45:00Z", acuity: "2026-08-24T09:45:00Z" },
    },
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <AuthContext.Provider value={{ user: { user_id: "U-ADMIN", username: "admin", display_name: "Admin User", role: "admin" }, loading: false, error: null, signIn: vi.fn(), signOut: vi.fn() }}>
      <QueryClientProvider client={client}><DispatchPage patientId="P-1042" /></QueryClientProvider>
    </AuthContext.Provider>,
  );
}

describe("DispatchPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/dispatch/evaluation")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(evaluation) });
      }
      if (url.endsWith("/dispatch/confirm")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ state: "assigned", assignment_id: "N-SARAH", prototype_label: evaluation.prototype_label }) });
      }
      if (url.endsWith("/dispatch/override")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ state: "assigned", assignment_id: "N-REED", prototype_label: evaluation.prototype_label }) });
      }
      if (url.endsWith("/dispatch/retry")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ...evaluation, status: "ready", recommendation_nurse_id: "N-SARAH" }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ events: [] }) });
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    cleanup();
  });

  it("shows ranked recommendation first, alternative evidence, and explicit decision controls", async () => {
    renderPage();

    expect(await screen.findByText("Dispatch review")).toBeInTheDocument();
    expect(screen.getByText("Recommended nurse")).toBeInTheDocument();
    expect(screen.getAllByText("Sarah Lee").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.93").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Availability").length).toBeGreaterThan(0);
    expect(screen.getByText("40% weight")).toBeInTheDocument();
    expect(screen.getByText("Boyd Hall")).toBeInTheDocument();
    expect(screen.getByText(/stale status/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm recommendation/i })).toBeEnabled();
    expect(screen.getByRole("button", { name: /override with reed clay/i })).toBeEnabled();
  });

  it("requires a reason and blocks stale or no-candidate decisions", async () => {
    renderPage();
    await screen.findByText("Dispatch review");

    const confirm = screen.getByRole("button", { name: /confirm recommendation/i });
    fireEvent.click(confirm);
    expect(screen.getByText("A brief reason is required.")).toBeInTheDocument();

    const reason = screen.getByLabelText(/decision reason/i);
    fireEvent.change(reason, { target: { value: "Doctor reviewed recommendation" } });
    fireEvent.click(screen.getByRole("button", { name: /confirm recommendation/i }));
    await waitFor(() => expect(screen.getByText("Dispatch decision recorded")).toBeInTheDocument());
  });

  it("shows a blocked no-candidate state without claiming a recommendation", async () => {
    cleanup();
    vi.unstubAllGlobals();
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.endsWith("/dispatch/evaluation")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            ...evaluation,
            status: "no_eligible_candidate",
            recommendation_nurse_id: null,
            recommendation_context: "No eligible candidate or fresh alert evidence; alert remains generated and unassigned.",
            candidates: [],
            exclusions: [
              {
                nurse_id: "N-BOYD",
                display_name: "Boyd Hall",
                eligible: false,
                exclusion_reasons: ["stale status", "unavailable"],
                rank: null,
                score: null,
                components: {},
                contributions: {},
                proximity_km: null,
                workload_active: null,
                workload_capacity: null,
                acuity_compatibility: null,
                freshness: { status: null, workload: null, proximity: null, acuity: null },
              },
            ],
          }),
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }));

    // Use fresh QueryClient to avoid cache from previous tests
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <AuthContext.Provider value={{ user: { user_id: "U-ADMIN", username: "admin", display_name: "Admin User", role: "admin" }, loading: false, error: null, signIn: vi.fn(), signOut: vi.fn() }}>
        <QueryClientProvider client={client}><DispatchPage patientId="P-1042" /></QueryClientProvider>
      </AuthContext.Provider>,
    );

    expect(await screen.findByRole("heading", { level: 3, name: /no eligible nurse/i })).toBeInTheDocument();
    expect(screen.getByText("Alert remains generated and unassigned")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry evaluation/i })).toBeEnabled();
    expect(screen.queryByRole("button", { name: /confirm recommendation/i })).not.toBeInTheDocument();
  });
});

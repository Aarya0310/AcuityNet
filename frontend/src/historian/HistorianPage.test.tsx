import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HistorianPage } from "./HistorianPage";
import type { HistorianResponse } from "../contracts/historian";

const baseTime = "2026-08-24T10:00:00Z";
const historian: HistorianResponse = {
  patient_id: "P-1042", patient_name: "Mara Chen", admission_id: "A-1042", admitted_at: baseTime, bed_id: "ICU-12", unit: "Simulated ICU",
  current_prediction: { patient_id: "P-1042", bed_id: "ICU-12", event: "Respiratory deterioration", probability: 0.91, score: 0.25, level: "critical", horizon_minutes: 30, timestamp: baseTime, current_vitals: {}, provenance: {}, prototype_label: "Simulated ICU environment - research prototype - not for clinical use", contract_version: "1", source_kind: "deterministic_fallback", source_version: "rules-v1", fallback_reason: "Model unavailable" },
  baseline_score: 0.25, contextual_status: "complete", contextual_score: 0.4,
  facts: [
    { fact_id: "D-P1042-01", category: "diagnosis", label: "Fictional respiratory condition", value: null, unit: null, effective_at: baseTime, source_kind: "synthetic", source_name: "seed" },
    { fact_id: "M-P1042-01", category: "medication", label: "Fictional inhaled support", value: null, unit: null, effective_at: baseTime, source_kind: "synthetic", source_name: "seed" },
    { fact_id: "L-P1042-01", category: "lab", label: "Oxygenation marker", value: "92", unit: "%", effective_at: baseTime, source_kind: "synthetic", source_name: "seed" },
    { fact_id: "E-P1042-01", category: "icu_event", label: "Prior respiratory observation", value: null, unit: null, effective_at: baseTime, source_kind: "synthetic", source_name: "seed" },
  ],
  rule_evaluations: [
    { rule_key: "diagnosis.respiratory_history", rule_name: "Respiratory history", rule_version: "rules.v1", category: "diagnosis", fact_id: "D-P1042-01", delta: 0.05, explanation: "Diagnosis context adjustment", evaluated_at: baseTime },
    { rule_key: "medication.respiratory_support", rule_name: "Respiratory support", rule_version: "rules.v1", category: "medication", fact_id: "M-P1042-01", delta: 0.03, explanation: "Medication context adjustment", evaluated_at: baseTime },
    { rule_key: "lab.oxygenation", rule_name: "Oxygenation", rule_version: "rules.v1", category: "lab", fact_id: "L-P1042-01", delta: 0.07, explanation: "Lab context adjustment", evaluated_at: baseTime },
    { rule_key: "icu_event.recent_deterioration", rule_name: "Recent deterioration", rule_version: "rules.v1", category: "icu_event", fact_id: "E-P1042-01", delta: 0.05, explanation: "ICU event context adjustment", evaluated_at: baseTime },
  ],
  missing_evidence: [], annotations: [], alert: null,
  timeline: [
    { entry_id: "fact-1", entry_type: "fact", occurred_at: "2026-08-24T09:00:00Z", title: "Patient context recorded", detail: "Diagnosis context" },
    { entry_id: "prediction-1", entry_type: "prediction", occurred_at: baseTime, title: "Prediction generated", detail: "Respiratory deterioration" },
  ],
  prototype_label: "Simulated ICU environment - research prototype - not for clinical use", provenance: "synthetic",
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><HistorianPage /></QueryClientProvider>);
}

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("HistorianPage", () => {
  it("renders the evidence chain, rules, provenance, and Doctor annotation refetch", async () => {
    let historianRequests = 0;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/historian")) {
        historianRequests += 1;
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(historian) });
      }
      if (url.endsWith("/annotations") && init?.method === "POST") return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ annotation_id: 1, author_id: "DR-LEE", text: "Review trajectory", created_at: baseTime, source_label: "Doctor annotation" }) });
      return Promise.reject(new Error(`Unexpected request: ${url}`));
    }));
    renderPage();
    expect(await screen.findByText("Mara Chen")).toBeInTheDocument();
    expect(screen.getByText("Diagnoses")).toBeInTheDocument();
    expect(screen.getByText("Fictional respiratory condition")).toBeInTheDocument();
    expect(screen.getByText("Baseline score")).toBeInTheDocument();
    expect(screen.getByText("0.40")).toBeInTheDocument();
    expect(screen.getByText("Respiratory history")).toBeInTheDocument();
    expect(screen.getAllByText("Simulated ICU environment - research prototype - not for clinical use")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "Evidence timeline" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add annotation" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Add a concise note"), { target: { value: "Review trajectory" } });
    fireEvent.click(screen.getByRole("button", { name: "Add annotation" }));
    await waitFor(() => expect(historianRequests).toBe(2));
  });

  it("shows baseline-only incomplete state without a contextual score", async () => {
    const incomplete = { ...historian, contextual_status: "incomplete" as const, contextual_score: null, missing_evidence: ["lab: required evidence missing"], rule_evaluations: [] };
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(incomplete) })));
    renderPage();
    expect(await screen.findByText("Baseline only")).toBeInTheDocument();
    expect(screen.getByText("Contextual risk unavailable")).toBeInTheDocument();
    expect(screen.getByText("lab: required evidence missing")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.queryByText("0.40")).not.toBeInTheDocument();
  });
});

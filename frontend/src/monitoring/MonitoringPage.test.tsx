import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MonitoringPage } from "./MonitoringPage";
import type { VitalObservation } from "../contracts/vitals";

const observation: VitalObservation = {
  patient_id: "P-1042",
  patient: { patient_id: "P-1042", display_name: "Avery Morgan", bed_id: "ICU-07", unit: "ICU" },
  bed_id: "ICU-07",
  unit: "ICU",
  sequence: 2,
  observed_at: "2026-08-24T10:00:00Z",
  received_at: "2026-08-24T10:00:05Z",
  spo2_percent: 94,
  heart_rate_bpm: 112,
  respiratory_rate_bpm: 24,
  systolic_bp_mmhg: 98,
  diastolic_bp_mmhg: 62,
  temperature_c: 38.1,
  provenance: {
    source_kind: "synthetic",
    source_name: "acuitynet-simulator",
    scenario_id: "p1042-deterioration",
    scenario_version: "1",
    is_live_bedside_feed: false,
  },
  freshness: "fresh",
  prototype_label: "Research prototype: simulated ICU data, not clinical advice.",
};

afterEach(cleanup);

describe("MonitoringPage", () => {
  it("renders P-1042 context, six vitals, timestamps, and safety metadata", () => {
    render(<MonitoringPage observation={observation} />);

    expect(screen.getByRole("heading", { name: /Avery Morgan/i })).toBeInTheDocument();
    expect(screen.getByText("ICU-07")).toBeInTheDocument();
    expect(screen.getByText("SpO2")).toBeInTheDocument();
    expect(screen.getByText("94 %")).toBeInTheDocument();
    expect(screen.getByText("112 bpm")).toBeInTheDocument();
    expect(screen.getByText("24 /min")).toBeInTheDocument();
    expect(screen.getByText("98 mmHg")).toBeInTheDocument();
    expect(screen.getByText("62 mmHg")).toBeInTheDocument();
    expect(screen.getByText("38.1 C")).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent?.replace(/\s+/g, " ").trim() === "Sequence: 2")).toBeInTheDocument();
    expect(screen.getByText(/acuitynet-simulator/)).toBeInTheDocument();
    expect(screen.getByText("Feed current")).toBeInTheDocument();
    expect(screen.getByText("Simulated ICU environment - research prototype - not for clinical use")).toBeInTheDocument();
  });

  it.each([
    ["fresh", "Feed current"],
    ["stale", "Feed stale"],
    ["disconnected", "Feed disconnected"],
    ["unavailable", "Feed unavailable"],
  ] as const)("renders an honest %s state without clinical claims", (freshness, stateLabel) => {
    render(<MonitoringPage observation={observation} freshnessOverride={freshness} />);

    expect(screen.getByText(stateLabel)).toBeInTheDocument();
    expect(screen.queryByText(/diagnos|treat|clinical recommendation/i)).not.toBeInTheDocument();
    expect(screen.getByText("Simulated ICU environment - research prototype - not for clinical use")).toBeInTheDocument();
  });
});

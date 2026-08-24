import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
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

function response(body: unknown) {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });
}

describe("MonitoringPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.endsWith("/api/v1/configuration")) {
        return response({ supported_intervals: [5, 10, 30, "manual"], default_interval: 10 });
      }
      if (url.endsWith("/vitals/advance")) {
        return response(observation);
      }
      return response(observation);
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

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

  it("renders exactly the server-configured refresh options", async () => {
    render(<MonitoringPage observation={observation} />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });

    expect(screen.getByRole("combobox", { name: /refresh interval/i })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "5 seconds" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "10 seconds" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "30 seconds" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Manual" })).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(4);
  });

  it("advances before reading current data for manual refresh", async () => {
    const fetchMock = vi.mocked(fetch);
    render(<MonitoringPage observation={observation} />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /refresh now/i }));
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toMatch(/vitals\/advance$/);
    expect(fetchMock.mock.calls[2][0]).toMatch(/vitals\/current$/);
  });

  it("advances on the configured interval and clears the timer when unmounted", async () => {
    const fetchMock = vi.mocked(fetch);
    const { unmount } = render(<MonitoringPage observation={observation} />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    fireEvent.change(screen.getByRole("combobox", { name: /refresh interval/i }), { target: { value: "5" } });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toMatch(/vitals\/advance$/);
    expect(fetchMock.mock.calls[2][0]).toMatch(/vitals\/current$/);

    unmount();
    await vi.advanceTimersByTimeAsync(5000);
    expect(fetchMock).toHaveBeenCalledTimes(3);
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

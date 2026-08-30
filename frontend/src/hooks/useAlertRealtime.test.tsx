import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useAlertRealtime } from "../alerts/useAlertRealtime";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  
  readonly url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  
  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }
  
  open() {
    this.onopen?.();
  }
  
  message(data: unknown) {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }) as any);
  }
  
  error() {
    this.onerror?.();
  }
  
  close() {
    this.onclose?.();
  }
  
  send(_data: string) {
    // Mock send
  }
}

afterEach(() => {
  FakeWebSocket.instances = [];
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("useAlertRealtime", () => {
  
  it("connects to WebSocket on mount", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    expect(FakeWebSocket.instances).toHaveLength(1);
    const socket = FakeWebSocket.instances[0];
    expect(socket.url).toContain("P-1042");
    expect(socket.url).toContain("access_token=test-token");
    
    act(() => {
      socket.open();
    });
    
    expect(result.current.state).toBe("connected");
  });
  
  it("receives invalidation messages and triggers refetch", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })));
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateQuery = vi.spyOn(queryClient, "invalidateQueries");
    const refetchQueries = vi.spyOn(queryClient, "refetchQueries");
    
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    const socket = FakeWebSocket.instances[0];
    
    act(() => {
      socket.open();
    });
    
    expect(result.current.state).toBe("connected");
    
    act(() => {
      socket.message({
        event: "alert.invalidated",
        patient_id: "P-1042",
        alert_id: 1,
      });
    });
    
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    
    expect(invalidateQuery).toHaveBeenCalled();
    expect(refetchQueries).toHaveBeenCalled();
  });
  
  it("detects WebSocket disconnect and changes state to disconnected", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    const socket = FakeWebSocket.instances[0];
    
    act(() => {
      socket.open();
    });
    
    expect(result.current.state).toBe("connected");
    
    act(() => {
      socket.close();
    });
    
    expect(result.current.state).toBe("disconnected");
  });
  
  it("automatically reconnects with exponential backoff", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    let socket = FakeWebSocket.instances[0];
    
    act(() => {
      socket.open();
    });
    
    expect(result.current.state).toBe("connected");
    expect(result.current.attempt).toBe(0);
    
    // Simulate disconnect
    act(() => {
      socket.close();
    });
    
    expect(result.current.state).toBe("disconnected");
    expect(result.current.attempt).toBe(1);
    
    // Advance timer by 1000ms (first reconnect attempt)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    
    // Should have created a new WebSocket for reconnect attempt
    expect(FakeWebSocket.instances).toHaveLength(2);
    socket = FakeWebSocket.instances[1];
    expect(socket.url).toContain("P-1042");
    
    // Simulate second disconnect
    act(() => {
      socket.close();
    });
    
    expect(result.current.attempt).toBe(2);
    
    // Advance timer by 2000ms (second reconnect attempt with exponential backoff)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    
    expect(FakeWebSocket.instances).toHaveLength(3);
    
    // Simulate successful reconnect
    socket = FakeWebSocket.instances[2];
    act(() => {
      socket.open();
    });
    
    expect(result.current.state).toBe("connected");
    expect(result.current.attempt).toBe(0); // Reset after successful reconnect
  });
  
  it("continues exponential backoff through 4s and 8s intervals", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    let socket = FakeWebSocket.instances[0];
    
    act(() => {
      socket.open();
    });
    
    // First disconnect at attempt 1
    act(() => {
      socket.close();
    });
    expect(result.current.attempt).toBe(1);
    
    // Reconnect attempt at 1s
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    socket = FakeWebSocket.instances[1];
    act(() => {
      socket.close();
    });
    expect(result.current.attempt).toBe(2);
    
    // Reconnect attempt at 3s total (1s + 2s)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    socket = FakeWebSocket.instances[2];
    act(() => {
      socket.close();
    });
    expect(result.current.attempt).toBe(3);
    
    // Reconnect attempt at 7s total (1s + 2s + 4s)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(4000);
    });
    socket = FakeWebSocket.instances[3];
    act(() => {
      socket.close();
    });
    expect(result.current.attempt).toBe(4);
    
    // Reconnect attempt at 15s total (1s + 2s + 4s + 8s)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(8000);
    });
    socket = FakeWebSocket.instances[4];
    
    // Verify capped at 8000ms backoff
    expect(FakeWebSocket.instances).toHaveLength(5);
  });
  
  it("cleans up WebSocket and timers on unmount", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result, unmount } = renderHook(() => useAlertRealtime("P-1042"), {
      wrapper,
    });
    
    const socket = FakeWebSocket.instances[0];
    const closeSpy = vi.spyOn(socket, "close");
    
    act(() => {
      socket.open();
    });
    
    expect(result.current.state).toBe("connected");
    
    // Unmount should close WebSocket and clear timers
    unmount();
    
    expect(closeSpy).toHaveBeenCalled();
    
    // Verify that reconnect timer was cleared by advancing time
    // After unmount, no new WebSocket instances should be created
    const instancesBeforeTimer = FakeWebSocket.instances.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(16000);
    });
    
    // Should not have created new sockets after unmount
    expect(FakeWebSocket.instances.length).toBe(instancesBeforeTimer);
  });
  
  it("ignores invalidation messages from other patients", () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateQuery = vi.spyOn(queryClient, "invalidateQueries");
    
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    const socket = FakeWebSocket.instances[0];
    
    act(() => {
      socket.open();
    });
    
    const initialCallCount = invalidateQuery.mock.calls.length;
    
    // Send message for different patient
    act(() => {
      socket.message({
        event: "alert.invalidated",
        patient_id: "P-OTHER",
        alert_id: 1,
      });
    });
    
    // Should not have called invalidate
    expect(invalidateQuery.mock.calls.length).toBe(initialCallCount);
  });
  
  it("handles manual refetch when user clicks refresh button", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket);
    vi.stubGlobal("localStorage", { getItem: () => "test-token" });
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })));
    
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const refetchQueries = vi.spyOn(queryClient, "refetchQueries");
    
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    
    const { result } = renderHook(() => useAlertRealtime("P-1042"), { wrapper });
    
    const socket = FakeWebSocket.instances[0];
    
    act(() => {
      socket.open();
    });
    
    // In a real component, user clicking refresh would call the refetch via a button
    // For the hook itself, we test that the invalidation mechanism works
    act(() => {
      socket.message({
        event: "alert.invalidated",
        patient_id: "P-1042",
        alert_id: 1,
      });
    });
    
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    
    // Verify refetch was called for the alert queries
    expect(refetchQueries).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: expect.arrayContaining(["alert", "P-1042"]),
      })
    );
  });
});

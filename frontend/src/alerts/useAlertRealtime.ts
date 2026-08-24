import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { getAccessToken, realtimeUrl } from "../api/client";
import type { RealtimeConnectionState, RealtimeInvalidation } from "../contracts/realtime";

const MAX_RECONNECTS = 5;

function isInvalidation(value: unknown, patientId: string): value is RealtimeInvalidation {
  if (!value || typeof value !== "object") return false;
  const message = value as Record<string, unknown>;
  return message.event === "alert.invalidated" && message.patient_id === patientId
    && (message.alert_id === undefined || typeof message.alert_id === "number")
    && (message.audit_id === undefined || typeof message.audit_id === "number");
}

export function useAlertRealtime(patientId: string, enabled = true) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<RealtimeConnectionState>("disconnected");
  const [attempt, setAttempt] = useState(0);
  const reconnectTimer = useRef<number | undefined>(undefined);
  const socketRef = useRef<WebSocket | undefined>(undefined);

  useEffect(() => {
    if (!enabled || !getAccessToken()) { setState("disconnected"); return; }
    let active = true;
    let reconnects = 0;
    const connect = () => {
      if (!active) return;
      setState("connecting");
      const socket = new WebSocket(realtimeUrl(patientId));
      socketRef.current = socket;
      socket.onopen = () => { if (active) { reconnects = 0; setAttempt(0); setState("connected"); } };
      socket.onmessage = (event) => {
        try {
          const message: unknown = JSON.parse(event.data);
          if (!isInvalidation(message, patientId)) return;
          void queryClient.invalidateQueries({ queryKey: ["alert", patientId] });
          void queryClient.invalidateQueries({ queryKey: ["alert-events", patientId] });
          void queryClient.invalidateQueries({ queryKey: ["alert-audit", patientId] });
          void queryClient.refetchQueries({ queryKey: ["alert", patientId], type: "active" });
          void queryClient.refetchQueries({ queryKey: ["alert-events", patientId], type: "active" });
          void queryClient.refetchQueries({ queryKey: ["alert-audit", patientId], type: "active" });
        } catch { setState("error"); }
      };
      socket.onerror = () => { if (active) setState("error"); };
      socket.onclose = () => {
        if (!active) return;
        setState("disconnected");
        if (reconnects >= MAX_RECONNECTS) return;
        reconnects += 1;
        setAttempt(reconnects);
        reconnectTimer.current = window.setTimeout(connect, Math.min(1000 * 2 ** (reconnects - 1), 8000));
      };
    };
    connect();
    return () => {
      active = false;
      if (reconnectTimer.current !== undefined) window.clearTimeout(reconnectTimer.current);
      socketRef.current?.close();
      socketRef.current = undefined;
    };
  }, [enabled, patientId, queryClient]);

  return { state, attempt };
}
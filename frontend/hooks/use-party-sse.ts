"use client";

import { useEffect, useRef, useCallback } from "react";
import { getAccessToken } from "@/lib/api";

type SSEHandler = (event: string, data: unknown) => void;

/**
 * Hook to subscribe to real-time SSE events for a party.
 *
 * Uses native EventSource with auth token in query param.
 * EventSource handles SSE parsing, reconnection, and buffering natively.
 */
export function usePartySSE(partyCode: string | null, onEvent: SSEHandler) {
    const onEventRef = useRef(onEvent);

    useEffect(() => {
        onEventRef.current = onEvent;
    }, [onEvent]);
    const esRef = useRef<EventSource | null>(null);

    const connect = useCallback(() => {
        if (!partyCode) return;

        const token = getAccessToken();
        if (!token) return;

        // Close any previous connection
        if (esRef.current) {
            esRef.current.close();
            esRef.current = null;
        }

        // Auto-detect backend URL from browser hostname (LAN support)
        const apiBase = `http://${window.location.hostname}:8000`;
        const url = `${apiBase}/api/sse/${partyCode}?token=${encodeURIComponent(token)}`;

        console.log("[SSE] Connecting to", url);
        const es = new EventSource(url);
        esRef.current = es;

        // Listen for all event types we care about
        const eventTypes = [
            "balance_update",
            "transaction_new",
            "joint_payment_update",
            "party_update",
        ];

        for (const eventType of eventTypes) {
            es.addEventListener(eventType, (e: MessageEvent) => {
                console.log(`[SSE] Received event: ${eventType}`, e.data);
                try {
                    const parsed = JSON.parse(e.data);
                    onEventRef.current(eventType, parsed);
                } catch {
                    onEventRef.current(eventType, e.data);
                }
            });
        }

        es.onopen = () => {
            console.log("[SSE] Connection opened");
        };

        es.onerror = (err) => {
            console.warn("[SSE] Connection error, will auto-reconnect", err);
            // EventSource auto-reconnects by default
        };
    }, [partyCode]);

    useEffect(() => {
        connect();
        return () => {
            if (esRef.current) {
                console.log("[SSE] Closing connection");
                esRef.current.close();
                esRef.current = null;
            }
        };
    }, [connect]);
}

"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Mic,
  MicOff,
  PhoneOff,
  Volume2,
  Loader2,
  Wifi,
  WifiOff,
  AlertCircle,
  Radio,
  Activity,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type VoiceState =
  | "idle"
  | "connecting"
  | "listening"
  | "thinking"
  | "speaking"
  | "error"
  | "disconnected";

interface VoiceSessionConfig {
  sessionId?: string;       // meeting context; undefined = workspace mode
  participantName?: string;
  language?: "english" | "hindi";
}

interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: VoiceSessionConfig;
  meetingTitle?: string;
}

// ---------------------------------------------------------------------------
// LiveKit status → VoiceState mapping helper (used after connecting)
// ---------------------------------------------------------------------------

const STATE_LABELS: Record<VoiceState, string> = {
  idle: "Ready",
  connecting: "Connecting…",
  listening: "Listening…",
  thinking: "Thinking…",
  speaking: "Speaking…",
  error: "Error",
  disconnected: "Disconnected",
};

const STATE_COLORS: Record<VoiceState, string> = {
  idle: "text-slate-500",
  connecting: "text-amber-600",
  listening: "text-indigo-600",
  thinking: "text-purple-600",
  speaking: "text-emerald-600",
  error: "text-rose-600",
  disconnected: "text-slate-400",
};

const STATE_BG: Record<VoiceState, string> = {
  idle: "bg-slate-100",
  connecting: "bg-amber-50",
  listening: "bg-indigo-50",
  thinking: "bg-purple-50",
  speaking: "bg-emerald-50",
  error: "bg-rose-50",
  disconnected: "bg-slate-50",
};

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function VoiceModal({ isOpen, onClose, config, meetingTitle }: VoiceModalProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [liveKitConfigured, setLiveKitConfigured] = useState<boolean | null>(null);
  const [transcript, setTranscript] = useState<Array<{ role: "user" | "assistant"; text: string }>>([]);

  // LiveKit room reference (loaded dynamically to avoid SSR issues)
  const roomRef = useRef<unknown>(null);
  const localTrackRef = useRef<unknown>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll transcript
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  // Check LiveKit configuration status on mount
  useEffect(() => {
    if (!isOpen) return;
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_BASE}/api/v1/voice/livekit/status`)
      .then((r) => r.json())
      .then((data) => setLiveKitConfigured(data.configured))
      .catch(() => setLiveKitConfigured(false));
  }, [isOpen]);

  const cleanup = useCallback(() => {
    try {
      const track = localTrackRef.current as { stop?: () => void } | null;
      track?.stop?.();
    } catch { /* ignore */ }
    try {
      const room = roomRef.current as { disconnect?: () => void } | null;
      room?.disconnect?.();
    } catch { /* ignore */ }
    localTrackRef.current = null;
    roomRef.current = null;
  }, []);

  // Connect to LiveKit voice session
  const connect = useCallback(async () => {
    setVoiceState("connecting");
    setErrorMessage(null);

    try {
      // 1. Request a token from our backend
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const tokenRes = await fetch(`${API_BASE}/api/v1/voice/livekit/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: config.sessionId || null,
          language: config.language || "english",
          participant_name: config.participantName || "RecallAI User",
        }),
      });

      if (!tokenRes.ok) {
        const err = await tokenRes.json().catch(() => ({}));
        throw new Error(err.detail || `Token request failed (${tokenRes.status})`);
      }

      const { token, livekit_url } = await tokenRes.json();

      // 2. Dynamically import livekit-client (browser-only)
      const { Room, RoomEvent, Track } = await import("livekit-client");

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      roomRef.current = room;

      // 3. Wire up room events → voice state
      room.on(RoomEvent.Connected, () => {
        setVoiceState("listening");
      });

      room.on(RoomEvent.Disconnected, () => {
        setVoiceState("disconnected");
        cleanup();
      });

      room.on(RoomEvent.ParticipantConnected, () => {
        // Voice agent joined
      });

      // Track remote audio to detect speaking state
      room.on(RoomEvent.TrackSubscribed, (track: unknown, _pub: unknown, participant: unknown) => {
        const t = track as { kind: string };
        const p = participant as { isAgent?: boolean };
        if (t.kind === Track.Kind.Audio && p.isAgent) {
          setVoiceState("speaking");
        }
      });

      room.on(RoomEvent.TrackUnsubscribed, (_track: unknown, _pub: unknown, participant: unknown) => {
        const p = participant as { isAgent?: boolean };
        if (p.isAgent) {
          setVoiceState("listening");
        }
      });

      // Data channel for transcript messages from the agent
      room.on(RoomEvent.DataReceived, (data: Uint8Array) => {
        try {
          const msg = JSON.parse(new TextDecoder().decode(data)) as {
            type?: string;
            role?: string;
            text?: string;
          };
          if (msg.type === "transcript") {
            setTranscript((prev) => [
              ...prev,
              { role: (msg.role as "user" | "assistant") || "assistant", text: msg.text || "" },
            ]);
            if (msg.role === "assistant") {
              setVoiceState("speaking");
            }
          } else if (msg.type === "thinking") {
            setVoiceState("thinking");
          } else if (msg.type === "listening") {
            setVoiceState("listening");
          }
        } catch {
          // Non-JSON data payload — ignore
        }
      });

      // 4. Connect to the room
      await room.connect(livekit_url, token);

      // 5. Publish local microphone track
      const { createLocalAudioTrack } = await import("livekit-client");
      const localTrack = await createLocalAudioTrack({
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      });
      localTrackRef.current = localTrack;
      await room.localParticipant.publishTrack(localTrack);

    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to connect to voice session.";
      setErrorMessage(message);
      setVoiceState("error");
    }
  }, [config, cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    setVoiceState("idle");
    setTranscript([]);
  }, [cleanup]);

  const toggleMute = useCallback(() => {
    try {
      const track = localTrackRef.current as { mute?: () => void; unmute?: () => void; isMuted?: boolean } | null;
      if (!track) return;
      if (isMuted) {
        track.unmute?.();
      } else {
        track.mute?.();
      }
      setIsMuted((prev) => !prev);
    } catch { /* ignore */ }
  }, [isMuted]);

  // Cleanup when modal closes
  useEffect(() => {
    if (!isOpen) {
      disconnect();
    }
    return () => {
      if (!isOpen) cleanup();
    };
  }, [isOpen, disconnect, cleanup]);

  if (!isOpen) return null;

  const isConnected = voiceState !== "idle" && voiceState !== "disconnected" && voiceState !== "error" && voiceState !== "connecting";
  const isActive = isConnected;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
        onClick={() => {
          if (!isActive) onClose();
        }}
      />

      {/* Modal Panel */}
      <div className="relative z-10 w-full max-w-md mx-4 bg-white rounded-2xl shadow-2xl border border-slate-200/80 overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
        {/* Header */}
        <div className={`px-5 py-4 border-b border-slate-100 flex items-center justify-between ${STATE_BG[voiceState]}`}>
          <div className="flex items-center gap-2.5">
            <div className={`p-1.5 rounded-lg ${voiceState === "listening" ? "bg-indigo-100" : voiceState === "speaking" ? "bg-emerald-100" : voiceState === "thinking" ? "bg-purple-100" : "bg-slate-100"}`}>
              <Radio className={`w-4 h-4 ${STATE_COLORS[voiceState]}`} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">RecallAI Voice</h2>
              <p className="text-[11px] text-slate-500 truncate max-w-[220px]">
                {config.sessionId ? (meetingTitle || "Meeting Context") : "Workspace Context"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Status badge */}
            <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold flex items-center gap-1 ${STATE_BG[voiceState]} ${STATE_COLORS[voiceState]} border border-current/20`}>
              {voiceState === "connecting" && <Loader2 className="w-3 h-3 animate-spin" />}
              {voiceState === "listening" && <Activity className="w-3 h-3 animate-pulse" />}
              {voiceState === "speaking" && <Volume2 className="w-3 h-3 animate-pulse" />}
              {voiceState === "thinking" && <Loader2 className="w-3 h-3 animate-spin" />}
              {STATE_LABELS[voiceState]}
            </span>
          </div>
        </div>

        {/* LiveKit not configured warning */}
        {liveKitConfigured === false && (
          <div className="mx-5 mt-4 p-3 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-2.5 text-xs text-amber-800">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">LiveKit not configured</p>
              <p className="text-amber-700 mt-0.5">
                Set <code className="bg-amber-100 px-1 rounded">LIVEKIT_URL</code>,{" "}
                <code className="bg-amber-100 px-1 rounded">LIVEKIT_API_KEY</code>, and{" "}
                <code className="bg-amber-100 px-1 rounded">LIVEKIT_API_SECRET</code> in your{" "}
                <code className="bg-amber-100 px-1 rounded">.env</code> to enable real-time voice.
              </p>
            </div>
          </div>
        )}

        {/* Error message */}
        {voiceState === "error" && errorMessage && (
          <div className="mx-5 mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-800">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span className="font-medium">{errorMessage}</span>
          </div>
        )}

        {/* Transcript area */}
        <div
          ref={scrollRef}
          className="px-5 py-4 min-h-[160px] max-h-[280px] overflow-y-auto space-y-2.5"
        >
          {transcript.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-36 text-center text-slate-400 space-y-2">
              <Mic className="w-8 h-8 text-slate-300 stroke-1" />
              <p className="text-xs font-medium text-slate-500">
                {voiceState === "idle" || voiceState === "disconnected"
                  ? "Press Start to begin a voice conversation"
                  : voiceState === "connecting"
                  ? "Connecting to voice session…"
                  : "Listening for your question…"}
              </p>
              <p className="text-[11px] text-slate-400">
                {config.sessionId
                  ? `Context: ${meetingTitle || "this meeting"}`
                  : "Context: all meetings in your workspace"}
              </p>
            </div>
          ) : (
            transcript.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-sm"
                      : "bg-slate-100 text-slate-800 rounded-bl-sm"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Visualizer bar */}
        {isConnected && (
          <div className="px-5 pb-2 flex items-center justify-center gap-0.5 h-8">
            {Array.from({ length: 24 }).map((_, i) => (
              <div
                key={i}
                className={`w-1 rounded-full transition-all duration-150 ${
                  voiceState === "listening"
                    ? "bg-indigo-400"
                    : voiceState === "speaking"
                    ? "bg-emerald-400"
                    : voiceState === "thinking"
                    ? "bg-purple-300"
                    : "bg-slate-200"
                }`}
                style={{
                  height: voiceState === "listening" || voiceState === "speaking"
                    ? `${8 + Math.abs(Math.sin((Date.now() / 200) + i * 0.7)) * 20}px`
                    : "4px",
                }}
              />
            ))}
          </div>
        )}

        {/* Controls */}
        <div className="px-5 pb-5 pt-2 flex items-center justify-between gap-3">
          {/* Mute toggle */}
          <button
            type="button"
            onClick={toggleMute}
            disabled={!isConnected}
            className={`p-2.5 rounded-xl border transition-all ${
              isConnected
                ? isMuted
                  ? "bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100"
                  : "bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200"
                : "bg-slate-50 border-slate-100 text-slate-300 cursor-not-allowed"
            }`}
            title={isMuted ? "Unmute microphone" : "Mute microphone"}
          >
            {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          {/* Main action button */}
          <div className="flex-1">
            {!isConnected && voiceState !== "connecting" ? (
              <button
                type="button"
                onClick={connect}
                disabled={liveKitConfigured === false}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white rounded-xl text-sm font-semibold shadow-sm transition-all flex items-center justify-center gap-2"
              >
                <Mic className="w-4 h-4" />
                Start Voice
              </button>
            ) : voiceState === "connecting" ? (
              <div className="w-full py-2.5 px-4 bg-amber-50 border border-amber-200 text-amber-700 rounded-xl text-sm font-semibold flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Connecting…
              </div>
            ) : (
              <button
                type="button"
                onClick={disconnect}
                className="w-full py-2.5 px-4 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-semibold shadow-sm transition-all flex items-center justify-center gap-2"
              >
                <PhoneOff className="w-4 h-4" />
                End Session
              </button>
            )}
          </div>

          {/* Close button */}
          <button
            type="button"
            onClick={() => {
              disconnect();
              onClose();
            }}
            className="p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 hover:bg-slate-100 transition-colors"
            title="Close"
          >
            <PhoneOff className="w-4 h-4" />
          </button>
        </div>

        {/* Footer context */}
        <div className="px-5 pb-4 flex items-center gap-1.5 text-[11px] text-slate-400">
          {voiceState === "disconnected" || voiceState === "idle" ? (
            <WifiOff className="w-3 h-3" />
          ) : (
            <Wifi className="w-3 h-3 text-emerald-500" />
          )}
          <span>
            {voiceState === "idle" || voiceState === "disconnected"
              ? "Not connected"
              : "Live voice session · RecallAI"}
          </span>
        </div>
      </div>
    </div>
  );
}

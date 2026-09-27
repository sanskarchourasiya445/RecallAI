import { apiClient } from "./client";
import { ChatRequest, ChatResponse, ChatHistoryResponse } from "@/types/chat";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiClient<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: request.session_id,
      message: request.message,
      top_k: request.top_k || 4,
    }),
  });
}

export async function getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
  return apiClient<ChatHistoryResponse>(`/api/v1/chat/history?session_id=${encodeURIComponent(sessionId)}`);
}

export async function clearChatHistory(sessionId: string): Promise<{ session_id: string; cleared: boolean }> {
  return apiClient<{ session_id: string; cleared: boolean }>(
    `/api/v1/chat/history?session_id=${encodeURIComponent(sessionId)}`,
    {
      method: "DELETE",
    }
  );
}

export interface StreamCallbacks {
  onMetadata?: (meta: Partial<ChatResponse>) => void;
  onToken?: (delta: string) => void;
  onDone?: (fullResponse: ChatResponse) => void;
  onError?: (error: Error) => void;
}

export async function sendChatMessageStream(
  request: ChatRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/chat/stream`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        session_id: request.session_id,
        message: request.message,
        top_k: request.top_k || 4,
      }),
      signal,
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Streaming failed (${res.status}): ${errText}`);
    }

    if (!res.body) {
      throw new Error("No response body available for streaming");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;
        const blockLines = block.split("\n");
        let eventType = "message";
        let dataStr = "";

        for (const line of blockLines) {
          if (line.startsWith("event:")) {
            eventType = line.replace("event:", "").trim();
          } else if (line.startsWith("data:")) {
            dataStr = line.replace("data:", "").trim();
          }
        }

        if (eventType === "metadata" && callbacks.onMetadata) {
          try {
            const meta = JSON.parse(dataStr);
            callbacks.onMetadata(meta);
          } catch (e) {
            console.error("Failed to parse metadata SSE event:", e);
          }
        } else if (eventType === "token" && callbacks.onToken) {
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.delta) {
              callbacks.onToken(parsed.delta);
            }
          } catch (e) {
            console.error("Failed to parse token SSE event:", e);
          }
        } else if (eventType === "done" && callbacks.onDone) {
          try {
            const finalData = JSON.parse(dataStr);
            callbacks.onDone(finalData);
          } catch (e) {
            console.error("Failed to parse done SSE event:", e);
          }
        } else if (eventType === "error") {
          try {
            const errJson = JSON.parse(dataStr);
            throw new Error(errJson.error || "Streaming error occurred");
          } catch (e) {
            throw e instanceof Error ? e : new Error(dataStr);
          }
        }
      }
    }
  } catch (err: unknown) {
    if (callbacks.onError) {
      callbacks.onError(err instanceof Error ? err : new Error(String(err)));
    } else {
      throw err;
    }
  }
}

import { apiClient } from "./client";
import {
  WorkspaceChatRequest,
  WorkspaceChatResponse,
  WorkspaceMemoryResponse,
} from "@/types/workspace";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendWorkspaceChat(
  request: WorkspaceChatRequest
): Promise<WorkspaceChatResponse> {
  return apiClient<WorkspaceChatResponse>("/api/v1/workspace/chat", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getWorkspaceMemory(): Promise<WorkspaceMemoryResponse> {
  return apiClient<WorkspaceMemoryResponse>("/api/v1/workspace/memory");
}

export interface WorkspaceStreamCallbacks {
  onMetadata?: (meta: Partial<WorkspaceChatResponse>) => void;
  onToken?: (delta: string) => void;
  onDone?: (fullResponse: WorkspaceChatResponse) => void;
  onError?: (error: Error) => void;
}

export async function sendWorkspaceChatStream(
  request: WorkspaceChatRequest,
  callbacks: WorkspaceStreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/workspace/chat/stream`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(request),
      signal,
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Workspace streaming failed (${res.status}): ${errText}`);
    }

    if (!res.body) {
      throw new Error("No response body available for workspace streaming");
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
            console.error("Failed to parse workspace metadata SSE event:", e);
          }
        } else if (eventType === "token" && callbacks.onToken) {
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.delta) {
              callbacks.onToken(parsed.delta);
            }
          } catch (e) {
            console.error("Failed to parse workspace token SSE event:", e);
          }
        } else if (eventType === "done" && callbacks.onDone) {
          try {
            const finalData = JSON.parse(dataStr);
            callbacks.onDone(finalData);
          } catch (e) {
            console.error("Failed to parse workspace done SSE event:", e);
          }
        } else if (eventType === "error") {
          try {
            const errJson = JSON.parse(dataStr);
            throw new Error(errJson.error || "Workspace streaming error occurred");
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

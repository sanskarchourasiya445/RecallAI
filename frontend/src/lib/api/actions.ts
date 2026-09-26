import { apiClient } from "./client";
import {
  ActionExecutionResponse,
  PendingActionsResponse,
} from "@/types/action";

export async function getAvailableTools(): Promise<Record<string, unknown>[]> {
  return apiClient<Record<string, unknown>[]>("/api/v1/actions/tools");
}

export async function getPendingActions(sessionId?: string): Promise<PendingActionsResponse> {
  const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  return apiClient<PendingActionsResponse>(`/api/v1/actions/pending${query}`);
}

export async function executeAction(
  sessionId: string,
  action: string,
  parameters: Record<string, unknown> = {}
): Promise<ActionExecutionResponse> {
  return apiClient<ActionExecutionResponse>("/api/v1/actions", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      action,
      parameters,
    }),
  });
}

export async function confirmAction(
  actionId: string,
  sessionId: string
): Promise<ActionExecutionResponse> {
  return apiClient<ActionExecutionResponse>(`/api/v1/actions/${encodeURIComponent(actionId)}/confirm`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function rejectAction(
  actionId: string,
  sessionId: string,
  reason: string = "User declined"
): Promise<ActionExecutionResponse> {
  return apiClient<ActionExecutionResponse>(`/api/v1/actions/${encodeURIComponent(actionId)}/reject`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, reason }),
  });
}

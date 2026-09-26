import { apiClient } from "./client";
import { ChatRequest, ChatResponse } from "@/types/chat";

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

import { apiClient } from "./client";
import { GlobalSearchResponse } from "@/types/search";

export interface SearchWorkspaceParams {
  query: string;
  limit?: number;
  session_id?: string;
}

export async function searchWorkspace({
  query,
  limit = 15,
  session_id,
}: SearchWorkspaceParams): Promise<GlobalSearchResponse> {
  const params = new URLSearchParams();
  params.set("q", query);
  if (limit) params.set("limit", String(limit));
  if (session_id) params.set("session_id", session_id);

  return apiClient<GlobalSearchResponse>(`/api/v1/search?${params.toString()}`);
}

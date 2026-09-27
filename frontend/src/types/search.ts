export interface SearchResultItem {
  session_id: string;
  meeting_title: string;
  source_type: string;
  timestamp: string;
  start_seconds: number;
  end_seconds: number;
  snippet: string;
  match_type: "transcript" | "decision" | "action_item" | "dilemma" | string;
  relevance_score: number;
  evidence_id: string;
  chunk_index?: number;
}

export interface GlobalSearchResponse {
  query: string;
  total: number;
  results: SearchResultItem[];
  session_id?: string | null;
}

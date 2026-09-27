export interface CitationItem {
  evidence_id: string;
  time_range: string;
  chunk_index?: number;
  source?: string;
  score?: number | null;
}

export interface EvidenceItem {
  evidence_id: string;
  text: string;
  time_range: string;
  start_seconds: number;
  end_seconds: number;
  chunk_index: number;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  top_k?: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: CitationItem[];
  evidence: EvidenceItem[];
  resolved_query: string;
  intent: "question" | "action" | "clarify";
  refused: boolean;
  requires_confirmation: boolean;
  pending_action_id?: string | null;
}

export interface ChatTurnItem {
  turn_id: number;
  user_message: string;
  assistant_message: string;
  evidence_ids?: string[];
  resolved_query?: string | null;
  timestamp?: string | null;
}

export interface ChatHistoryResponse {
  session_id: string;
  turns: ChatTurnItem[];
}

export interface UIMessage {
  id: string;
  sender: "user" | "ai";
  content: string;
  timestamp: string;
  citations?: CitationItem[];
  evidence?: EvidenceItem[];
  intent?: string;
  requiresConfirmation?: boolean;
  pendingActionId?: string | null;
  isStreaming?: boolean;
  actionStatus?: "pending" | "confirmed" | "rejected";
  actionResult?: string;
  error?: boolean;
}


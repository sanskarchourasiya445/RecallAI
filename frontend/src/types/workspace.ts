export interface WorkspaceCitationItem {
  evidence_id: string;
  session_id: string;
  meeting_title: string;
  time_range: string;
  start_seconds: number;
  citation_label: string;
  snippet: string;
  score?: number | null;
}

export interface WorkspaceChatRequest {
  message: string;
  top_k?: number;
}

export interface WorkspaceChatResponse {
  answer: string;
  citations: WorkspaceCitationItem[];
  sources: Array<{
    session_id: string;
    title: string;
    source: string;
  }>;
  resolved_query: string;
  refused: boolean;
}

export interface WorkspaceDecisionItem {
  decision_id: string;
  session_id: string;
  meeting_title: string;
  decision: string;
  rationale?: string | null;
  evidence?: string | null;
  timestamp?: string | null;
  status: string;
}

export interface WorkspaceActionItemData {
  action_id: string;
  session_id: string;
  meeting_title: string;
  task: string;
  owner?: string | null;
  deadline?: string | null;
  evidence?: string | null;
  timestamp?: string | null;
  status: string;
}

export interface WorkspaceOpenQuestionItem {
  question_id: string;
  session_id: string;
  meeting_title: string;
  question: string;
  context?: string | null;
  evidence?: string | null;
  timestamp?: string | null;
  status: string;
}

export interface WorkspaceEntityMention {
  session_id: string;
  meeting_title: string;
  timestamp?: string | null;
  context: string;
}

export interface WorkspaceEntityItem {
  entity_name: string;
  entity_type: string;
  mentions: WorkspaceEntityMention[];
}

export interface WorkspaceMemoryResponse {
  overview: {
    total_meetings: number;
    total_decisions: number;
    total_action_items: number;
    total_open_questions: number;
    tracked_topics: string[];
    tracked_people: string[];
  };
  decisions: WorkspaceDecisionItem[];
  action_items: WorkspaceActionItemData[];
  open_questions: WorkspaceOpenQuestionItem[];
  entities: WorkspaceEntityItem[];
}

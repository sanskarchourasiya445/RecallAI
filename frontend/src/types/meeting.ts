export interface ActionItem {
  task: string;
  owner?: string | null;
  deadline?: string | null;
  status: string;
  priority?: "High" | "Medium" | "Low";
  evidence?: string | null;
  timestamp?: string | null;
}

export interface DecisionItem {
  decision: string;
  evidence?: string | null;
  timestamp?: string | null;
  author?: string | null;
  status?: string;
}

export interface OpenQuestionItem {
  question: string;
  evidence?: string | null;
  timestamp?: string | null;
  author?: string | null;
}

export interface MeetingSource {
  id: string;
  title: string;
  type: "youtube" | "transcript" | "pdf" | "spreadsheet";
  subtitle: string;
  meta: string;
  url?: string;
}

export interface MeetingDetailResponse {
  session_id: string;
  title: string;
  transcript: string;
  summary: string;
  status: string;
  segments_count?: number;
  is_demo?: boolean;
}

export interface MeetingProcessResponse {
  session_id: string;
  title: string;
  status: string;
  transcript_available: boolean;
  summary_available: boolean;
  indexed: boolean;
  action_items_count: number;
  decisions_count: number;
  open_questions_count: number;
}

export interface MeetingIngestResponse {
  session_id: string;
  source: string;
  source_type: "youtube" | "upload";
  status: string;
  message: string;
}

export interface SummaryResponse {
  session_id: string;
  title: string;
  summary: string;
}

export interface ActionItemsResponse {
  session_id: string;
  action_items: ActionItem[];
  total: number;
}

export interface DecisionsResponse {
  session_id: string;
  key_decisions: DecisionItem[];
  total: number;
}

export interface OpenQuestionsResponse {
  session_id: string;
  open_questions: OpenQuestionItem[];
  total: number;
}

export interface MeetingListItem {
  session_id: string;
  title: string;
  status: string;
  created_at?: string | null;
  source?: string | null;
  source_type?: "youtube" | "upload" | string;
  duration?: string | null;
  participants_count?: number;
  summary_preview?: string | null;
  decisions_count: number;
  actions_count: number;
  open_questions_count: number;
  is_demo: boolean;
}

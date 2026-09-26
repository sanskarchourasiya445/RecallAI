export interface ActionExecutionRequest {
  session_id: string;
  action: string;
  parameters?: Record<string, unknown>;
}

export interface ActionExecutionResponse {
  success: boolean;
  tool_name: string;
  message: string;
  resource_id?: string | null;
  requires_confirmation: boolean;
  pending_action_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface PendingActionItem {
  action_id: string;
  session_id: string;
  tool_name: string;
  risk_level: string;
  preview_summary: string;
  expires_at: number;
}

export interface PendingActionsResponse {
  session_id?: string | null;
  pending_actions: PendingActionItem[];
}

export interface ToolDefinition {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  isHighRisk?: boolean;
}

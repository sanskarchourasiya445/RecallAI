import { apiClient } from "./client";
import {
  MeetingDetailResponse,
  MeetingProcessResponse,
  MeetingIngestResponse,
  SummaryResponse,
  ActionItemsResponse,
  DecisionsResponse,
  OpenQuestionsResponse,
} from "@/types/meeting";

export async function loadDemoMeeting(): Promise<MeetingDetailResponse> {
  return apiClient<MeetingDetailResponse>("/api/v1/meetings/demo", {
    method: "POST",
  });
}

export async function getMeeting(sessionId: string): Promise<MeetingDetailResponse> {
  return apiClient<MeetingDetailResponse>(`/api/v1/meetings/${encodeURIComponent(sessionId)}`);
}

export async function getMeetingSummary(sessionId: string): Promise<SummaryResponse> {
  return apiClient<SummaryResponse>(`/api/v1/meetings/${encodeURIComponent(sessionId)}/summary`);
}

export async function getMeetingActions(sessionId: string): Promise<ActionItemsResponse> {
  return apiClient<ActionItemsResponse>(`/api/v1/meetings/${encodeURIComponent(sessionId)}/actions`);
}

export async function getMeetingDecisions(sessionId: string): Promise<DecisionsResponse> {
  return apiClient<DecisionsResponse>(`/api/v1/meetings/${encodeURIComponent(sessionId)}/decisions`);
}

export async function getMeetingOpenQuestions(sessionId: string): Promise<OpenQuestionsResponse> {
  return apiClient<OpenQuestionsResponse>(`/api/v1/meetings/${encodeURIComponent(sessionId)}/open-questions`);
}

export async function ingestYouTube(url: string): Promise<MeetingIngestResponse> {
  return apiClient<MeetingIngestResponse>("/api/v1/meetings/youtube", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function ingestUpload(file: File): Promise<MeetingIngestResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient<MeetingIngestResponse>("/api/v1/meetings/upload", {
    method: "POST",
    body: formData,
  });
}

export async function processMeeting(
  sessionId: string,
  language: string = "english"
): Promise<MeetingProcessResponse> {
  return apiClient<MeetingProcessResponse>(`/api/v1/meetings/${encodeURIComponent(sessionId)}/process`, {
    method: "POST",
    body: JSON.stringify({ language }),
  });
}

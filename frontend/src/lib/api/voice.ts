import { apiClient } from "./client";

export async function transcribeVoice(audioFile: File, language: string = "english"): Promise<{ text: string }> {
  const formData = new FormData();
  formData.append("audio", audioFile);
  formData.append("language", language);

  return apiClient<{ text: string }>("/api/v1/voice/transcribe", {
    method: "POST",
    body: formData,
  });
}

export async function synthesizeVoice(text: string, voice?: string): Promise<Blob> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const res = await fetch(`${API_BASE_URL}/api/v1/voice/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!res.ok) {
    throw new Error(`Voice synthesis failed with status ${res.status}`);
  }
  return res.blob();
}

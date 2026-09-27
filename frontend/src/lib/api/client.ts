const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export interface ApiOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiClient<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers: HeadersInit = {
    Accept: "application/json",
    ...(options.headers || {}),
  };

  // Only set Content-Type to application/json if body is not FormData
  if (!(options.body instanceof FormData) && !("Content-Type" in (headers as Record<string, string>))) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const { timeoutMs = 60000, signal, ...fetchOptions } = options;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: signal || controller.signal,
    });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiError(`Request timed out after ${timeoutMs / 1000}s`, 408);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let errorData: unknown = null;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }

    const errObj = errorData && typeof errorData === "object" ? (errorData as Record<string, unknown>) : null;
    const message =
      (errObj && (errObj.detail || errObj.error)) ||
      `API request failed with status ${response.status}`;

    throw new ApiError(String(message), response.status, errorData);
  }

  return response.json() as Promise<T>;
}

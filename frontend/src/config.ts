export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const SESSION_ID_KEY = "brainlattice_session_id";
export const GEMINI_KEY_STORAGE = "brainlattice_gemini_key";
export const OPENAI_KEY_STORAGE = "brainlattice_openai_key";

export function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_ID_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  return sessionId;
}

export function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const sessionId = getSessionId();
  const apiKey = localStorage.getItem(GEMINI_KEY_STORAGE) || "";
  const openAiKey = localStorage.getItem(OPENAI_KEY_STORAGE) || "";
  
  const headers = new Headers(init?.headers);
  headers.set("X-User-Id", sessionId);
  if (apiKey) {
    headers.set("X-Gemini-API-Key", apiKey);
  }
  if (openAiKey) {
    headers.set("X-OpenAI-API-Key", openAiKey);
  }
  
  return fetch(input, {
    ...init,
    headers
  });
}

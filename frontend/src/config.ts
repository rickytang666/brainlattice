export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const SESSION_ID_KEY = "brainlattice_session_id";
export const GEMINI_KEY_STORAGE = "brainlattice_gemini_key";
export const OPENAI_KEY_STORAGE = "brainlattice_openai_key";
export const OPENROUTER_KEY_STORAGE = "brainlattice_openrouter_key";
export const SPOTLIGHT_DISMISSED_KEY = "bl_spotlight_dismissed";

export function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_ID_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  return sessionId;
}

// apiFetch isn't a hook, so it reads clerk off window instead of calling useAuth()
async function getClerkToken(): Promise<string | null> {
  const clerk = (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string | null> } } }).Clerk;
  if (!clerk?.session) return null;
  try {
    return await clerk.session.getToken();
  } catch {
    return null;
  }
}

export async function apiFetch(input: RequestInfo | URL, init?: RequestInit, clerkUserId?: string | null): Promise<Response> {
  const apiKey = localStorage.getItem(GEMINI_KEY_STORAGE) || "";
  const openAiKey = localStorage.getItem(OPENAI_KEY_STORAGE) || "";
  const openRouterKey = localStorage.getItem(OPENROUTER_KEY_STORAGE) || "";

  const headers = new Headers(init?.headers);

  // the backend ignores X-User-Id when a token is present; signed-out users send the uuid
  if (clerkUserId) {
    const token = await getClerkToken();
    // falling back to the anonymous uuid here would silently hide the user's projects
    if (!token) throw new Error("Your session expired. Sign in again.");
    headers.set("Authorization", `Bearer ${token}`);
  } else {
    headers.set("X-User-Id", getSessionId());
  }

  if (apiKey) {
    headers.set("X-Gemini-API-Key", apiKey);
  }
  if (openAiKey) {
    headers.set("X-OpenAI-API-Key", openAiKey);
  }
  if (openRouterKey) {
    headers.set("X-OpenRouter-API-Key", openRouterKey);
  }

  return fetch(input, {
    ...init,
    headers
  });
}

export function shouldShowSpotlight(): boolean {
  return !localStorage.getItem(SPOTLIGHT_DISMISSED_KEY);
}

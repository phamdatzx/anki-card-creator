import type {
  CardType,
  CreateResponse,
  Deck,
  LookupResponse,
  SyncState,
} from "./types";

/** Same origin in production; Vite proxies /api to the server in dev. */
const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ??
  "";

const TOKEN_KEY = "word-inbox-token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Storage unavailable; the session lasts until reload.
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Nothing stored.
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let memoryToken: string | null = null;

async function request<T>(
  path: string,
  body?: unknown,
  auth = true,
  method: string = body === undefined ? "GET" : "POST",
): Promise<T> {
  const headers = new Headers();
  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getToken() ?? memoryToken;
    if (!token) {
      throw new ApiError(401, "Sign in again.");
    }
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE}/api${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : null;
    throw new ApiError(
      response.status,
      typeof detail === "string" ? detail : `Request failed (${response.status})`,
    );
  }
  return data as T;
}

export async function login(password: string): Promise<void> {
  const data = await request<{ token: string }>("/login", { password }, false);
  memoryToken = data.token;
  setToken(data.token);
}

export function decks(): Promise<{ decks: Deck[]; defaultDeckId: number | null }> {
  return request("/decks");
}

export function status(): Promise<{ sync: SyncState }> {
  return request("/status");
}

export function lookup(type: CardType, input: string): Promise<LookupResponse> {
  return request("/lookup", { type, input });
}

export function createCards(
  type: CardType,
  deckId: number,
  payload: unknown,
): Promise<CreateResponse> {
  return request("/cards", { type, deckId, payload });
}

export function createDeck(name: string): Promise<{ deck: Deck; sync: SyncState }> {
  return request("/decks", { name });
}

export function renameDeck(id: number, name: string): Promise<{ deck: Deck; sync: SyncState }> {
  return request(`/decks/${id}`, { name }, true, "PATCH");
}

export function deleteDeck(
  id: number,
): Promise<{ deleted: { name: string; cards: number }; sync: SyncState }> {
  return request(`/decks/${id}`, undefined, true, "DELETE");
}

export function sync(forceDownload = false): Promise<{ sync: SyncState }> {
  return request("/sync", { forceDownload });
}

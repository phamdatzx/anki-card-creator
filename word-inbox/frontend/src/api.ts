import type { Word, WordType } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
  /\/$/,
  "",
) || "http://localhost:8080";

const TOKEN_KEY = "word-inbox-token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getToken();
    if (!token) {
      throw new ApiError(401, "Not logged in");
    }
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { error: text };
    }
  }
  if (!response.ok) {
    const message =
      data && typeof data === "object" && "error" in data
        ? String((data as { error: unknown }).error)
        : `Request failed (${response.status})`;
    throw new ApiError(response.status, message);
  }
  return data as T;
}

export async function login(password: string): Promise<string> {
  const data = await request<{ token: string }>(
    "/login",
    { method: "POST", body: JSON.stringify({ password }) },
    false,
  );
  setToken(data.token);
  return data.token;
}

export async function listWords(): Promise<Word[]> {
  const data = await request<{ words: Word[] }>("/words");
  return data.words ?? [];
}

export async function createWord(
  input: string,
  type: WordType,
): Promise<Word> {
  return request<Word>("/words", {
    method: "POST",
    body: JSON.stringify({ input, type }),
  });
}

export async function deleteWord(id: string): Promise<void> {
  await request<void>(`/words/${id}`, { method: "DELETE" });
}

export { ApiError };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
};

export type Repository = {
  id: string;
  github_url: string;
  name: string;
  status: string;
  created_at: string;
};

export type IndexResponse = {
  status: string;
  message: string;
};

export type RepositoryStatusResponse = {
  status: string;
};

export type EmbedResponse = {
  message: string;
  chunks: number;
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;

    try {
      const body = await res.json();
      detail =
        typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail ?? body);
    } catch {
      // response body wasn't JSON - fall back to statusText
    }

    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  const data = await handleResponse<LoginResponse>(res);
  setToken(data.access_token);
  return data;
}

export async function register(
  name: string,
  email: string,
  password: string,
): Promise<User> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });

  return handleResponse<User>(res);
}

export async function getRepositories(): Promise<Repository[]> {
  const res = await fetch(`${API_URL}/repositories`, {
    headers: authHeaders(),
  });

  return handleResponse<Repository[]>(res);
}

export async function addRepository(githubUrl: string): Promise<Repository> {
  const res = await fetch(`${API_URL}/repositories`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify({ github_url: githubUrl }),
  });

  return handleResponse<Repository>(res);
}

export async function indexRepository(
  repoId: string,
): Promise<IndexResponse> {
  const res = await fetch(`${API_URL}/repositories/${repoId}/index`, {
    method: "POST",
    headers: authHeaders(),
  });

  return handleResponse<IndexResponse>(res);
}

export async function embedRepository(
  repoId: string,
): Promise<EmbedResponse> {
  const res = await fetch(`${API_URL}/repositories/${repoId}/embed`, {
    method: "POST",
    headers: authHeaders(),
  });

  return handleResponse<EmbedResponse>(res);
}

export async function getRepositoryStatus(
  repoId: string,
): Promise<RepositoryStatusResponse> {
  const res = await fetch(`${API_URL}/repositories/${repoId}/status`, {
    headers: authHeaders(),
  });

  return handleResponse<RepositoryStatusResponse>(res);
}

export type AgentStreamEvent =
  | { type: "thinking"; step: number }
  | { type: "tool_call"; tool: string; arguments: Record<string, unknown> }
  | { type: "tool_result"; tool: string; success: boolean }
  | { type: "answer"; content: string }
  | { type: "error"; message: string };

export async function askStream(
  repoId: string,
  question: string,
  onEvent: (event: AgentStreamEvent) => void
){
  const res = await fetch(`${API_URL}/repositories/${repoId}/agent/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed with status ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();

  let buffer = "";
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for(const part of parts) {
      const trimmed = part.trim();
      if(trimmed.startsWith("data: ")) {
        const jsonStr = trimmed.slice(6);
        try {
          const event = JSON.parse(jsonStr);
          onEvent(event);
        } catch (error) {
          console.error("Error parsing JSON:", error);
        }
      }
    }
  }
}
import type { AskResult, AuditEvent, ConversationMessage, DocumentItem, OrganizationUser, Overview, User } from "./types";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ user: User }>("/api/auth/me"),
  logout: () => request<{ status: string }>("/api/auth/logout", { method: "POST" }),
  documents: () => request<{ documents: DocumentItem[] }>("/api/documents"),
  overview: () => request<Overview>("/api/admin/overview"),
  users: () => request<{ users: OrganizationUser[] }>("/api/admin/users"),
  updateUser: (id: string, role: User["role"], department: string) =>
    request<{ user: OrganizationUser }>(`/api/admin/users/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify({ role, department }),
    }),
  uploadDocument: (document: { title: string; category: string; source: string; access_level: string; department?: string; content: string }) =>
    request<{ document: DocumentItem }>("/api/admin/documents", {
      method: "POST",
      body: JSON.stringify(document),
    }),
  updateDocumentStatus: (id: string, status: "Published" | "Archived") =>
    request<{ document: DocumentItem }>(`/api/admin/documents/${encodeURIComponent(id)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  audit: () => request<{ events: AuditEvent[] }>("/api/admin/audit"),
  ask: (question: string, history: ConversationMessage[] = []) =>
    request<AskResult>("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question, history }),
    }),
};

export type Role =
  | "organization_admin"
  | "knowledge_manager"
  | "hr"
  | "manager"
  | "employee"
  | "compliance_auditor";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  department: string;
  organization: string;
}

export interface DocumentItem {
  id: string;
  title: string;
  category: string;
  source: string;
  status: string;
  access_level: string;
  updated_at: string;
  snippet: string;
}

export interface Overview {
  documents: number;
  indexed: number;
  users: number | null;
  events: number | null;
  sources: { name: string; status: string; connected: boolean }[];
}

export interface AskResult {
  answer: string;
  sources: { id: string; title: string; source: string; snippet: string; pages: number[] }[];
  mode: "gemini" | "no_evidence" | "conversation";
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ConversationTurn {
  question: string;
  result: AskResult;
}

export interface AuditEvent {
  action: string;
  created_at: string;
  name: string;
  email: string;
}

export interface OrganizationUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  department: string;
  created_at: string;
}

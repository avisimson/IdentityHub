export interface User {
  id: string;
  email: string;
  full_name: string;
  auth_provider: "local" | "google";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface JiraStatus {
  connected: boolean;
  cloud_id?: string;
  jira_site_url?: string;
}

export interface JiraProject {
  id: string;
  key: string;
  name: string;
  avatar_url?: string;
}

export interface JiraIssueType {
  id: string;
  name: string;
  is_default: boolean;
}

export interface TicketCreatedBy {
  id: string;
  full_name: string;
}

export interface Ticket {
  id: string;
  jira_ticket_key: string;
  jira_ticket_url: string;
  summary: string;
  issue_type: string;
  source: "ui" | "api" | "blog_digest";
  created_at: string;
  created_by: TicketCreatedBy;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  key: string;
  created_at: string;
}

export interface BlogDigestSchedule {
  hour: number;
  minute: number;
  timezone: string;
  enabled: boolean;
}

export interface BlogDigestTriggerResult {
  detail: string;
  ticket_key: string | null;
}

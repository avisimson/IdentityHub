import { http, HttpResponse } from "msw";
import type {
  AuthResponse,
  User,
  JiraStatus,
  JiraProject,
  JiraIssueType,
  Ticket,
  ApiKey,
  ApiKeyCreated,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Mock data — shapes match the exact API contracts from backend_hld.md §6
// ---------------------------------------------------------------------------

export const mockUser: User = {
  id: "user-1",
  email: "test@example.com",
  full_name: "Test User",
  auth_provider: "local",
};

export const mockAuthResponse: AuthResponse = {
  access_token: "mock-access-token",
  token_type: "bearer",
  user: mockUser,
};

export const mockJiraStatus: JiraStatus = {
  connected: true,
  cloud_id: "cloud-123",
  jira_site_url: "https://test.atlassian.net",
};

export const mockProjects: JiraProject[] = [
  { id: "10001", key: "PROJ", name: "Project Alpha", avatar_url: "https://example.com/avatar.png" },
  { id: "10002", key: "SEC", name: "Security", avatar_url: undefined },
];

export const mockIssueTypes: JiraIssueType[] = [
  { id: "1", name: "Bug", is_default: false },
  { id: "2", name: "Task", is_default: true },
  { id: "3", name: "Story", is_default: false },
];

export const mockTicket: Ticket = {
  id: "ticket-1",
  jira_ticket_key: "PROJ-42",
  jira_ticket_url: "https://test.atlassian.net/browse/PROJ-42",
  summary: "Fix broken auth flow",
  issue_type: "Bug",
  source: "ui",
  created_at: "2026-04-01T10:00:00Z",
  created_by: { id: "user-1", full_name: "Test User" },
};

export const mockApiKeys: ApiKey[] = [
  {
    id: "key-1",
    name: "CI Pipeline Key",
    key_prefix: "idhub_abc1",
    created_at: "2026-03-15T08:00:00Z",
    last_used_at: "2026-04-07T14:30:00Z",
  },
  {
    id: "key-2",
    name: "Scanner Key",
    key_prefix: "idhub_def2",
    created_at: "2026-04-01T12:00:00Z",
    last_used_at: null,
  },
];

export const mockApiKeyCreated: ApiKeyCreated = {
  id: "key-3",
  name: "New Key",
  key: "idhub_full_secret_key_shown_once",
  created_at: "2026-04-08T09:00:00Z",
};

// ---------------------------------------------------------------------------
// MSW Request Handlers
// ---------------------------------------------------------------------------

export const handlers = [
  // Auth
  http.post(`${API_BASE}/auth/register`, () =>
    HttpResponse.json(mockAuthResponse, { status: 201 }),
  ),

  http.post(`${API_BASE}/auth/login`, () =>
    HttpResponse.json(mockAuthResponse),
  ),

  http.post(`${API_BASE}/auth/google`, () =>
    HttpResponse.json(mockAuthResponse),
  ),

  http.post(`${API_BASE}/auth/refresh`, () =>
    HttpResponse.json(mockAuthResponse),
  ),

  http.get(`${API_BASE}/auth/me`, () =>
    HttpResponse.json(mockUser),
  ),

  http.post(`${API_BASE}/auth/logout`, () =>
    HttpResponse.json({ detail: "Logged out" }),
  ),

  // Jira
  http.get(`${API_BASE}/jira/status`, () =>
    HttpResponse.json(mockJiraStatus),
  ),

  http.get(`${API_BASE}/jira/projects`, () =>
    HttpResponse.json({ projects: mockProjects }),
  ),

  http.get(`${API_BASE}/jira/projects/:key/issue-types`, () =>
    HttpResponse.json({ issue_types: mockIssueTypes }),
  ),

  http.post(`${API_BASE}/jira/tickets`, () =>
    HttpResponse.json(mockTicket, { status: 201 }),
  ),

  http.get(`${API_BASE}/jira/tickets`, () =>
    HttpResponse.json({ tickets: [mockTicket] }),
  ),

  // API Keys
  http.get(`${API_BASE}/api-keys`, () =>
    HttpResponse.json({ api_keys: mockApiKeys }),
  ),

  http.post(`${API_BASE}/api-keys`, () =>
    HttpResponse.json(mockApiKeyCreated, { status: 201 }),
  ),

  http.delete(`${API_BASE}/api-keys/:id`, () =>
    HttpResponse.json({ detail: "Deleted" }),
  ),
];

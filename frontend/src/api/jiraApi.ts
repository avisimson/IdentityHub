import api from "./client";
import type { JiraStatus, JiraProject, JiraIssueType, Ticket } from "@/types";

export interface JiraAuthUrlResponse {
  authorization_url: string;
  state: string;
}

export interface JiraProjectsResponse {
  projects: JiraProject[];
}

export interface JiraIssueTypesResponse {
  issue_types: JiraIssueType[];
}

export interface CreateTicketRequest {
  project_key: string;
  summary: string;
  description: string;
  issue_type: string;
}

export interface TicketsResponse {
  tickets: Ticket[];
}

export async function getAuthUrl(): Promise<JiraAuthUrlResponse> {
  const { data } = await api.get<JiraAuthUrlResponse>("/jira/auth/url");
  return data;
}

export async function getStatus(): Promise<JiraStatus> {
  const { data } = await api.get<JiraStatus>("/jira/status");
  return data;
}

export async function getProjects(): Promise<JiraProjectsResponse> {
  const { data } = await api.get<JiraProjectsResponse>("/jira/projects");
  return data;
}

export async function getIssueTypes(
  projectKey: string,
): Promise<JiraIssueTypesResponse> {
  const { data } = await api.get<JiraIssueTypesResponse>(
    `/jira/projects/${projectKey}/issue-types`,
  );
  return data;
}

export async function createTicket(
  payload: CreateTicketRequest,
): Promise<Ticket> {
  const { data } = await api.post<Ticket>("/jira/tickets", payload);
  return data;
}

export async function getRecentTickets(
  projectKey: string,
  limit = 10,
): Promise<TicketsResponse> {
  const { data } = await api.get<TicketsResponse>("/jira/tickets", {
    params: { project_key: projectKey, limit },
  });
  return data;
}

export async function disconnect(): Promise<{ detail: string }> {
  const { data } = await api.delete<{ detail: string }>("/jira/connection");
  return data;
}

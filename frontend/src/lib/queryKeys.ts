export const queryKeys = {
  auth: {
    user: ["auth", "user"] as const,
  },
  jira: {
    status: ["jira", "status"] as const,
    projects: ["jira", "projects"] as const,
    issueTypes: (projectKey: string) =>
      ["jira", "issueTypes", projectKey] as const,
    tickets: (projectKey: string) =>
      ["jira", "tickets", projectKey] as const,
  },
  apiKeys: {
    list: ["apiKeys"] as const,
  },
  blogDigest: {
    schedule: ["blogDigest", "schedule"] as const,
  },
} as const;

import { useQuery } from "@tanstack/react-query";
import { getIssueTypes } from "@/api/jiraApi";
import { queryKeys } from "@/lib/queryKeys";

export function useIssueTypes(projectKey: string | undefined) {
  return useQuery({
    queryKey: queryKeys.jira.issueTypes(projectKey ?? ""),
    queryFn: () => getIssueTypes(projectKey!),
    enabled: !!projectKey,
  });
}

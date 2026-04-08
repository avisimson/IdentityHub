import { useQuery } from "@tanstack/react-query";
import { getStatus } from "@/api/jiraApi";
import { queryKeys } from "@/lib/queryKeys";

export function useJiraStatus() {
  return useQuery({
    queryKey: queryKeys.jira.status,
    queryFn: getStatus,
  });
}

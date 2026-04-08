import { useQuery } from "@tanstack/react-query";
import { getProjects } from "@/api/jiraApi";
import { queryKeys } from "@/lib/queryKeys";
import { useJiraStatus } from "./useJiraStatus";

export function useProjects() {
  const { data: status } = useJiraStatus();

  return useQuery({
    queryKey: queryKeys.jira.projects,
    queryFn: getProjects,
    enabled: !!status?.connected,
  });
}

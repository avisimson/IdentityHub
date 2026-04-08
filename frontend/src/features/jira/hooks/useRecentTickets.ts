import { useQuery } from "@tanstack/react-query";
import { getRecentTickets } from "@/api/jiraApi";
import { queryKeys } from "@/lib/queryKeys";

export function useRecentTickets(projectKey: string | undefined) {
  return useQuery({
    queryKey: queryKeys.jira.tickets(projectKey ?? ""),
    queryFn: () => getRecentTickets(projectKey!),
    enabled: !!projectKey,
  });
}

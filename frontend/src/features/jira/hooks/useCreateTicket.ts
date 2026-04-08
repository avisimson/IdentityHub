import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { createTicket, type CreateTicketRequest, type TicketsResponse } from "@/api/jiraApi";
import { queryKeys } from "@/lib/queryKeys";
import { getErrorCode, getErrorMessage } from "@/lib/errors";

export function useCreateTicket(projectKey: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTicketRequest) => createTicket(data),
    onSuccess: (newTicket) => {
      queryClient.setQueryData<TicketsResponse>(
        queryKeys.jira.tickets(projectKey),
        (old) => ({
          tickets: [newTicket, ...(old?.tickets ?? [])].slice(0, 10),
        }),
      );
      toast.success(`Ticket ${newTicket.jira_ticket_key} created`);
    },
    onError: (error) => {
      const code = getErrorCode(error);
      if (code === "JIRA_PROJECT_NOT_FOUND") {
        queryClient.invalidateQueries({ queryKey: queryKeys.jira.projects });
      }
      toast.error(getErrorMessage(error));
    },
  });
}

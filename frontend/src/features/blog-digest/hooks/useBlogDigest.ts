import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getSchedule,
  triggerDigest,
  updateSchedule,
} from "@/api/blogDigestApi";
import { getErrorCode, getErrorMessage } from "@/lib/errors";
import { queryKeys } from "@/lib/queryKeys";

export function useBlogDigestSchedule() {
  return useQuery({
    queryKey: queryKeys.blogDigest.schedule,
    queryFn: getSchedule,
  });
}

export function useUpdateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.blogDigest.schedule,
      });
      toast.success("Schedule updated");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

export function useTriggerDigest() {
  return useMutation({
    mutationFn: triggerDigest,
    onSuccess: (data) => {
      if (data.ticket_key) {
        toast.success(`Blog digest ticket created: ${data.ticket_key}`);
      } else {
        toast.success("Blog digest completed");
      }
    },
    onError: (error) => {
      const code = getErrorCode(error);
      if (code === "JIRA_NOT_CONNECTED") {
        toast.error("Jira not connected — connect Jira first");
      } else {
        toast.error(getErrorMessage(error));
      }
    },
  });
}

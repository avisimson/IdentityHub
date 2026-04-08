import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { createKey, type CreateApiKeyRequest } from "@/api/apiKeysApi";
import { queryKeys } from "@/lib/queryKeys";
import { getErrorMessage } from "@/lib/errors";

export function useCreateApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateApiKeyRequest) => createKey(data),
    onSuccess: () => {
      toast.success("API key created");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys.list });
    },
  });
}

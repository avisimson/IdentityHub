import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { deleteKey } from "@/api/apiKeysApi";
import { queryKeys } from "@/lib/queryKeys";
import { getErrorMessage } from "@/lib/errors";
import type { ApiKeysListResponse } from "@/api/apiKeysApi";

export function useDeleteApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (keyId: string) => deleteKey(keyId),
    onMutate: async (keyId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.apiKeys.list });

      const previous = queryClient.getQueryData<ApiKeysListResponse>(
        queryKeys.apiKeys.list,
      );

      queryClient.setQueryData<ApiKeysListResponse>(
        queryKeys.apiKeys.list,
        (old) =>
          old
            ? { api_keys: old.api_keys.filter((k) => k.id !== keyId) }
            : old,
      );

      return { previous };
    },
    onSuccess: () => {
      toast.success("API key deleted");
    },
    onError: (error, _keyId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.apiKeys.list, context.previous);
      }
      toast.error(getErrorMessage(error));
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys.list });
    },
  });
}

import { useQuery } from "@tanstack/react-query";
import { listKeys } from "@/api/apiKeysApi";
import { queryKeys } from "@/lib/queryKeys";

export function useApiKeys() {
  return useQuery({
    queryKey: queryKeys.apiKeys.list,
    queryFn: listKeys,
    select: (data) => data.api_keys,
  });
}

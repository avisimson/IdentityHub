import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiKeyTable } from "@/features/api-keys/components/ApiKeyTable";
import { CreateKeyDialog } from "@/features/api-keys/components/CreateKeyDialog";
import { useApiKeys } from "@/features/api-keys/hooks/useApiKeys";

export function ApiKeysPage() {
  const { data: apiKeys, isLoading, isError, refetch } = useApiKeys();

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">API Keys</h1>
          <p className="text-sm text-muted-foreground">
            Manage API keys for programmatic access
          </p>
        </div>
        <CreateKeyDialog />
      </div>

      {isError ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 p-8 text-center">
          <AlertCircle className="size-8 text-destructive" />
          <p className="text-sm text-muted-foreground">
            Failed to load API keys.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-1.5 size-3" />
            Retry
          </Button>
        </div>
      ) : (
        <ApiKeyTable apiKeys={apiKeys} isLoading={isLoading} />
      )}
    </div>
  );
}

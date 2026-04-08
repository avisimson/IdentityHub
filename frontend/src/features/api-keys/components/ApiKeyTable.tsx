import { KeyRound } from "lucide-react";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiKeyRow } from "@/features/api-keys/components/ApiKeyRow";
import type { ApiKey } from "@/types";

interface ApiKeyTableProps {
  apiKeys: ApiKey[] | undefined;
  isLoading: boolean;
}

export function ApiKeyTable({ apiKeys, isLoading }: ApiKeyTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!apiKeys?.length) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-14 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted">
          <KeyRound className="size-5 text-muted-foreground/60" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            No API keys yet
          </p>
          <p className="text-xs text-muted-foreground/70">
            Generate one to enable programmatic access
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Key</TableHead>
            <TableHead>Last Used</TableHead>
            <TableHead className="text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {apiKeys.map((key) => (
            <ApiKeyRow key={key.id} apiKey={key} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

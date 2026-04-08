import { useState } from "react";
import { Trash2, Loader2, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ApiKey } from "@/types";
import { useDeleteApiKey } from "@/features/api-keys/hooks/useDeleteApiKey";
import { useClipboard } from "@/hooks/useClipboard";

interface ApiKeyRowProps {
  apiKey: ApiKey;
}

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return "Never";

  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

export function ApiKeyRow({ apiKey }: ApiKeyRowProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const deleteMutation = useDeleteApiKey();
  const { copy, hasCopied } = useClipboard();

  function handleDelete() {
    deleteMutation.mutate(apiKey.id, {
      onSettled: () => setConfirmOpen(false),
    });
  }

  return (
    <>
      <TableRow className="transition-colors hover:bg-muted/50">
        <TableCell className="font-medium">{apiKey.name}</TableCell>
        <TableCell>
          <div className="flex items-center gap-1.5">
            <code className="rounded-md bg-muted px-2 py-0.5 font-mono text-xs">
              {apiKey.key_prefix}...
            </code>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => copy(apiKey.key_prefix)}
              aria-label="Copy key prefix"
              className="text-muted-foreground hover:text-foreground"
            >
              {hasCopied ? (
                <Check className="size-3 text-green-600" />
              ) : (
                <Copy className="size-3" />
              )}
            </Button>
          </div>
        </TableCell>
        <TableCell className="text-sm text-muted-foreground">
          {formatRelativeTime(apiKey.last_used_at)}
        </TableCell>
        <TableCell className="text-right">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setConfirmOpen(true)}
            aria-label={`Delete ${apiKey.name}`}
            className="text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="size-3.5" />
          </Button>
        </TableCell>
      </TableRow>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete API Key</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{apiKey.name}</strong>?
              Any integrations using this key will stop working immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

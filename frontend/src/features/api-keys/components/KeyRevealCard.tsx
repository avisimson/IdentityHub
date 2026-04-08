import { Copy, Check, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useClipboard } from "@/hooks/useClipboard";

interface KeyRevealCardProps {
  rawKey: string;
  onDone: () => void;
}

export function KeyRevealCard({ rawKey, onDone }: KeyRevealCardProps) {
  const { copy, hasCopied } = useClipboard();

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-xl border-2 border-amber-300 bg-amber-50 p-4 text-amber-900 shadow-sm dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-amber-200 dark:bg-amber-800">
          <ShieldAlert className="size-4" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-semibold">Save this key now</p>
          <p className="text-xs leading-relaxed text-amber-800/80 dark:text-amber-200/80">
            This key will only be displayed once. Copy it and store it in a
            secure location. You will not be able to retrieve it later.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-xl border bg-muted/50 p-3">
        <code className="flex-1 select-all break-all font-mono text-sm">
          {rawKey}
        </code>
        <Button
          variant="outline"
          size="icon-sm"
          onClick={() => copy(rawKey)}
          aria-label="Copy API key"
          className="shrink-0"
        >
          {hasCopied ? (
            <Check className="size-3.5 text-green-600" />
          ) : (
            <Copy className="size-3.5" />
          )}
        </Button>
      </div>

      <Button className="w-full" onClick={onDone}>
        {hasCopied ? "Done" : "I've copied the key"}
      </Button>
    </div>
  );
}

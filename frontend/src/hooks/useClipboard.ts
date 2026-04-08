import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";

export function useClipboard(resetMs = 2000) {
  const [hasCopied, setHasCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const copy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text);
        setHasCopied(true);
        toast.success("Copied to clipboard");

        clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => setHasCopied(false), resetMs);
      } catch {
        toast.error("Failed to copy to clipboard");
      }
    },
    [resetMs],
  );

  return { copy, hasCopied };
}

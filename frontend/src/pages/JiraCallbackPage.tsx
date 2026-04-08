import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queryKeys";

export function JiraCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const handledRef = useRef(false);

  useEffect(() => {
    if (handledRef.current) return;
    handledRef.current = true;

    const status = searchParams.get("status");
    const message = searchParams.get("message");

    if (status === "success") {
      toast.success("Jira connected successfully");
      queryClient.invalidateQueries({ queryKey: queryKeys.jira.status });
      navigate("/dashboard", { replace: true });
    } else {
      toast.error(message || "Failed to connect Jira. Please try again.");
      navigate("/settings/jira", { replace: true });
    }
  }, [searchParams, navigate, queryClient]);

  return (
    <div className="flex flex-col items-center gap-4 py-20">
      <Loader2 className="size-8 animate-spin text-muted-foreground" />
      <p className="text-sm text-muted-foreground">
        Completing Jira connection...
      </p>
    </div>
  );
}

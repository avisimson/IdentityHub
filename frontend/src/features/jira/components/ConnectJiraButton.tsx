import { useState } from "react";
import { Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { getAuthUrl } from "@/api/jiraApi";
import { getErrorMessage } from "@/lib/errors";

export function ConnectJiraButton() {
  const [isLoading, setIsLoading] = useState(false);

  async function handleConnect() {
    setIsLoading(true);
    try {
      const { authorization_url } = await getAuthUrl();
      window.location.href = authorization_url;
    } catch (error) {
      toast.error(getErrorMessage(error));
      setIsLoading(false);
    }
  }

  return (
    <Button onClick={handleConnect} disabled={isLoading}>
      {isLoading ? (
        <Loader2 className="mr-2 size-4 animate-spin" />
      ) : (
        <ExternalLink className="mr-2 size-4" />
      )}
      Connect Jira
    </Button>
  );
}

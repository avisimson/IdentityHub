import { useState } from "react";
import { Loader2, Unlink } from "lucide-react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { disconnect } from "@/api/jiraApi";
import { queryKeys } from "@/lib/queryKeys";
import { getErrorMessage } from "@/lib/errors";

export function DisconnectJiraButton() {
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const queryClient = useQueryClient();

  async function handleDisconnect() {
    setIsLoading(true);
    try {
      await disconnect();
      queryClient.removeQueries({ queryKey: ["jira"] });
      await queryClient.invalidateQueries({ queryKey: queryKeys.jira.status });
      toast.success("Jira disconnected successfully");
      setOpen(false);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={<Button variant="destructive" />}
      >
        <Unlink className="mr-2 size-4" />
        Disconnect
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Disconnect Jira</DialogTitle>
          <DialogDescription>
            Are you sure you want to disconnect your Jira account? You will need
            to reconnect to create tickets.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDisconnect}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 size-4 animate-spin" />}
            Disconnect
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

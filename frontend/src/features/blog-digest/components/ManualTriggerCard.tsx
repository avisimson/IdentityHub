import { AlertCircle, CheckCircle2, Loader2, Newspaper } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useTriggerDigest } from "@/features/blog-digest/hooks/useBlogDigest";
import { getErrorCode, getErrorMessage } from "@/lib/errors";

export function ManualTriggerCard() {
  const { mutate, isPending, isSuccess, isError, error, data } =
    useTriggerDigest();

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Manual Trigger</CardTitle>
        <CardDescription>
          Scrape the latest Oasis Security blog post, generate an AI summary,
          and create a Jira ticket.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button onClick={() => mutate()} disabled={isPending}>
          {isPending ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Newspaper className="mr-2 size-4" />
              Run Now
            </>
          )}
        </Button>

        {isSuccess && data?.ticket_key && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle2 className="size-4 shrink-0" />
            Ticket created: {data.ticket_key}
          </div>
        )}

        {isError && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <div>
              <p>{getErrorMessage(error)}</p>
              {getErrorCode(error) === "JIRA_NOT_CONNECTED" && (
                <Link
                  to="/settings/jira"
                  className="mt-1 inline-block font-medium underline underline-offset-2"
                >
                  Go to Jira Settings
                </Link>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

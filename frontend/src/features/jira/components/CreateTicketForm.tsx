import { useCallback } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { IssueTypeSelect } from "./IssueTypeSelect";
import { useCreateTicket } from "@/features/jira/hooks/useCreateTicket";
import { getErrorMessage } from "@/lib/errors";

const createTicketSchema = z.object({
  summary: z
    .string()
    .min(1, "Summary is required")
    .max(255, "Summary must be under 255 characters"),
  description: z
    .string()
    .max(32000, "Description is too long")
    .optional()
    .or(z.literal("")),
  issue_type: z.string().min(1, "Issue type is required"),
});

type CreateTicketFormValues = z.infer<typeof createTicketSchema>;

interface CreateTicketFormProps {
  projectKey: string;
}

export function CreateTicketForm({ projectKey }: CreateTicketFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<CreateTicketFormValues>({
    resolver: zodResolver(createTicketSchema),
    defaultValues: { summary: "", description: "", issue_type: "Task" },
  });

  const createTicketMutation = useCreateTicket(projectKey);

  const onSubmit = useCallback(
    (data: CreateTicketFormValues) => {
      createTicketMutation.mutate(
        {
          project_key: projectKey,
          summary: data.summary,
          description: data.description ?? "",
          issue_type: data.issue_type || "Task",
        },
        { onSuccess: () => reset() },
      );
    },
    [createTicketMutation, projectKey, reset],
  );

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Create NHI Finding</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="summary">Summary</Label>
            <Input
              id="summary"
              placeholder="e.g. Stale service account: svc-deploy"
              aria-invalid={!!errors.summary}
              {...register("summary")}
            />
            {errors.summary && (
              <p className="text-sm text-destructive">
                {errors.summary.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="issue_type">Issue Type</Label>
            <Controller
              control={control}
              name="issue_type"
              render={({ field }) => (
                <IssueTypeSelect
                  projectKey={projectKey}
                  value={field.value}
                  onChange={field.onChange}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">
              Description{" "}
              <span className="text-muted-foreground">(optional)</span>
            </Label>
            <Textarea
              id="description"
              placeholder="Provide additional details..."
              rows={4}
              aria-invalid={!!errors.description}
              {...register("description")}
            />
            {errors.description && (
              <p className="text-sm text-destructive">
                {errors.description.message}
              </p>
            )}
          </div>

          {createTicketMutation.isError && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
              <AlertCircle className="size-4 shrink-0" />
              {getErrorMessage(createTicketMutation.error)}
            </div>
          )}

          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={createTicketMutation.isPending}
            >
              {createTicketMutation.isPending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Create Ticket
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

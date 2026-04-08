import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { KeyRevealCard } from "@/features/api-keys/components/KeyRevealCard";
import { useCreateApiKey } from "@/features/api-keys/hooks/useCreateApiKey";
import { getErrorMessage } from "@/lib/errors";
import type { ApiKeyCreated } from "@/types";

const createApiKeySchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(100, "Name must be under 100 characters"),
});

type CreateApiKeyValues = z.infer<typeof createApiKeySchema>;

export function CreateKeyDialog() {
  const [open, setOpen] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const createMutation = useCreateApiKey();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateApiKeyValues>({
    resolver: zodResolver(createApiKeySchema),
    defaultValues: { name: "" },
  });

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setCreatedKey(null);
      reset();
    }
    setOpen(nextOpen);
  }

  function onSubmit(data: CreateApiKeyValues) {
    createMutation.mutate(data, {
      onSuccess: (result) => {
        setCreatedKey(result);
      },
    });
  }

  function handleDone() {
    handleOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger
        render={<Button />}
      >
        Generate API Key
      </DialogTrigger>

      <DialogContent>
        {createdKey ? (
          <>
            <DialogHeader>
              <DialogTitle>API Key Created</DialogTitle>
              <DialogDescription>
                Your new API key has been created successfully.
              </DialogDescription>
            </DialogHeader>
            <KeyRevealCard rawKey={createdKey.key} onDone={handleDone} />
          </>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Generate API Key</DialogTitle>
              <DialogDescription>
                Give your key a descriptive name so you can identify it later.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-2 py-4">
              <Label htmlFor="key-name">Key Name</Label>
              <Input
                id="key-name"
                placeholder="e.g. CI Scanner"
                autoFocus
                aria-invalid={!!errors.name}
                {...register("name")}
              />
              {errors.name && (
                <p className="text-sm text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>

            {createMutation.isError && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
                <AlertCircle className="size-4 shrink-0" />
                {getErrorMessage(createMutation.error)}
              </div>
            )}

            <DialogFooter>
              <Button
                variant="outline"
                type="button"
                onClick={() => handleOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Create
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

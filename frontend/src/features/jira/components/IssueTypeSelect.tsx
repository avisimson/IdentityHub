import { useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useIssueTypes } from "@/features/jira/hooks/useIssueTypes";

interface IssueTypeSelectProps {
  projectKey: string | undefined;
  value: string;
  onChange: (value: string) => void;
}

export function IssueTypeSelect({
  projectKey,
  value,
  onChange,
}: IssueTypeSelectProps) {
  const { data, isLoading, isError, refetch } = useIssueTypes(projectKey);
  const issueTypes = data?.issue_types ?? [];

  useEffect(() => {
    if (!issueTypes.length) return;
    const defaultType = issueTypes.find((t) => t.is_default);
    if (defaultType && !value) {
      onChange(defaultType.name);
    }
  }, [issueTypes, value, onChange]);

  if (isError) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-destructive/20 bg-destructive/5 p-3">
        <AlertCircle className="size-4 shrink-0 text-destructive" />
        <p className="flex-1 text-sm text-muted-foreground">
          Failed to load issue types.
        </p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <Select value={value} onValueChange={(v) => onChange(v ?? "")} disabled={!projectKey}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={isLoading ? "Loading..." : "Select type"} />
      </SelectTrigger>
      <SelectContent>
        {issueTypes.map((type) => (
          <SelectItem key={type.id} value={type.name}>
            {type.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

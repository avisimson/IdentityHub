import { useState } from "react";
import { AlertCircle, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useProjects } from "@/features/jira/hooks/useProjects";

interface ProjectComboboxProps {
  value: string | undefined;
  onSelect: (projectKey: string) => void;
}

export function ProjectCombobox({ value, onSelect }: ProjectComboboxProps) {
  const [open, setOpen] = useState(false);
  const { data, isLoading, isError, refetch } = useProjects();
  const projects = data?.projects ?? [];

  if (isError) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-destructive/20 bg-destructive/5 p-3">
        <AlertCircle className="size-4 shrink-0 text-destructive" />
        <p className="flex-1 text-sm text-muted-foreground">
          Failed to load projects.
        </p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  const selected = projects.find((p) => p.key === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            className="w-full justify-between"
          />
        }
      >
        {selected ? (
          <span className="flex items-center gap-2 truncate">
            {selected.avatar_url && (
              <Avatar size="sm">
                <AvatarImage src={selected.avatar_url} alt={selected.name} />
                <AvatarFallback>{selected.key.slice(0, 2)}</AvatarFallback>
              </Avatar>
            )}
            <span className="font-medium">{selected.key}</span>
            <span className="text-muted-foreground">{selected.name}</span>
          </span>
        ) : (
          <span className="text-muted-foreground">
            {isLoading ? "Loading projects..." : "Select a project"}
          </span>
        )}
        <ChevronsUpDown className="ml-auto size-4 shrink-0 opacity-50" />
      </PopoverTrigger>
      <PopoverContent className="w-[var(--anchor-width)] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search projects..." />
          <CommandList>
            <CommandEmpty>No projects found.</CommandEmpty>
            <CommandGroup>
              {projects.map((project) => (
                <CommandItem
                  key={project.id}
                  value={`${project.key} ${project.name}`}
                  data-checked={value === project.key}
                  onSelect={() => {
                    onSelect(project.key);
                    setOpen(false);
                  }}
                >
                  {project.avatar_url && (
                    <Avatar size="sm">
                      <AvatarImage
                        src={project.avatar_url}
                        alt={project.name}
                      />
                      <AvatarFallback>
                        {project.key.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                  )}
                  <span className="font-medium">{project.key}</span>
                  <span className="text-muted-foreground">{project.name}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

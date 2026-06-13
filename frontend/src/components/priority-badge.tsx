import { cn, priorityColor } from "@/lib/utils";

export function PriorityBadge({ priority, className }: { priority: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        priorityColor(priority),
        className,
      )}
    >
      {priority}
    </span>
  );
}

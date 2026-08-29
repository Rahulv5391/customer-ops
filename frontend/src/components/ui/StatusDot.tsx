interface StatusDotProps { status: 'healthy' | 'degraded' | 'error' | 'online' | 'offline'; label?: string; }

const dotClasses: Record<string, string> = {
  healthy: 'bg-emerald-500', online: 'bg-emerald-500',
  degraded: 'bg-amber-500', error: 'bg-red-500', offline: 'bg-slate-400',
};

export function StatusDot({ status, label }: StatusDotProps) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full shrink-0 ${dotClasses[status] ?? 'bg-slate-400'}`} />
      {label && <span className="text-sm text-slate-600 dark:text-gray-400">{label}</span>}
    </span>
  );
}

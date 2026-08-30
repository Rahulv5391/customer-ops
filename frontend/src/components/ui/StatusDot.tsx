interface StatusDotProps { status: 'healthy' | 'degraded' | 'error' | 'online' | 'offline'; label?: string; }

const dotClasses: Record<string, string> = {
  healthy: 'bg-emerald-500 text-emerald-500', online: 'bg-emerald-500 text-emerald-500',
  degraded: 'bg-amber-500 text-amber-500', error: 'bg-red-500 text-red-500', offline: 'bg-slate-400 text-slate-400',
};

const live = new Set(['healthy', 'online']);

export function StatusDot({ status, label }: StatusDotProps) {
  const cls = dotClasses[status] ?? 'bg-slate-400 text-slate-400';
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`relative inline-flex w-2 h-2 rounded-full shrink-0 ${cls} ${live.has(status) ? 'status-pulse' : ''}`} />
      {label && <span className="text-sm text-slate-600 dark:text-gray-400 capitalize">{label}</span>}
    </span>
  );
}

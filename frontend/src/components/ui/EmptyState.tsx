import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface EmptyStateProps { icon?: LucideIcon; title: string; description?: string; action?: ReactNode; }

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in-up">
      {Icon && (
        <div className="w-14 h-14 rounded-2xl bg-brand-50 dark:bg-brand-900/20 flex items-center justify-center mb-4 ring-1 ring-brand-100 dark:ring-brand-800/40">
          <Icon size={24} className="text-brand-500 dark:text-brand-400" />
        </div>
      )}
      <h3 className="font-display text-sm font-semibold text-slate-800 dark:text-gray-200 mb-1">{title}</h3>
      {description && <p className="text-sm text-slate-500 dark:text-gray-400 max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

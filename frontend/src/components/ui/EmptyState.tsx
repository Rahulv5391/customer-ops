import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface EmptyStateProps { icon?: LucideIcon; title: string; description?: string; action?: ReactNode; }

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-gray-700 flex items-center justify-center mb-4">
          <Icon size={24} className="text-slate-400 dark:text-gray-500" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-slate-800 dark:text-gray-200 mb-1">{title}</h3>
      {description && <p className="text-sm text-slate-500 dark:text-gray-400 max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

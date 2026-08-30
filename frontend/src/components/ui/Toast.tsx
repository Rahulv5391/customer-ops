import { CheckCircle, XCircle, Info, X } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

const variantConfig = {
  success: { icon: CheckCircle, cls: 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-900/40 dark:border-emerald-800 dark:text-emerald-300', iconCls: 'text-emerald-500' },
  error:   { icon: XCircle,     cls: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/40 dark:border-red-800 dark:text-red-300',             iconCls: 'text-red-500'     },
  info:    { icon: Info,        cls: 'bg-brand-50 border-brand-200 text-brand-800 dark:bg-brand-900/40 dark:border-brand-800 dark:text-brand-300',     iconCls: 'text-brand-500'  },
};

export function ToastContainer() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => {
        const { icon: Icon, cls, iconCls } = variantConfig[t.variant];
        return (
          <div key={t.id} className={`flex items-start gap-3 p-3 pr-4 rounded-xl border text-sm pointer-events-auto min-w-[280px] max-w-sm animate-slide-in-right ${cls}`} style={{ boxShadow: 'var(--shadow-pop)' }}>
            <Icon size={18} className={`shrink-0 mt-0.5 ${iconCls}`} />
            <span className="flex-1">{t.message}</span>
            <button onClick={() => dismiss(t.id)} className="shrink-0 opacity-60 hover:opacity-100 transition"><X size={14} /></button>
          </div>
        );
      })}
    </div>
  );
}

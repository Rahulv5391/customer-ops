import { CheckCircle, XCircle, Info, X } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

const variantConfig = {
  success: { icon: CheckCircle, cls: 'bg-emerald-50 border-emerald-200 text-emerald-800', iconCls: 'text-emerald-500' },
  error:   { icon: XCircle,     cls: 'bg-red-50 border-red-200 text-red-800',             iconCls: 'text-red-500'     },
  info:    { icon: Info,        cls: 'bg-indigo-50 border-indigo-200 text-indigo-800',     iconCls: 'text-indigo-500'  },
};

export function ToastContainer() {
  const { toasts, dismiss } = useToast();
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map(t => {
        const { icon: Icon, cls, iconCls } = variantConfig[t.variant];
        return (
          <div key={t.id} className={`flex items-start gap-3 p-3 pr-4 rounded-xl border shadow-lg text-sm pointer-events-auto min-w-[280px] max-w-sm ${cls}`}>
            <Icon size={18} className={`shrink-0 mt-0.5 ${iconCls}`} />
            <span className="flex-1">{t.message}</span>
            <button onClick={() => dismiss(t.id)} className="shrink-0 opacity-60 hover:opacity-100 transition"><X size={14} /></button>
          </div>
        );
      })}
    </div>
  );
}

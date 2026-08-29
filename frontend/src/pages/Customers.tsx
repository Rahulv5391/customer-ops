import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { customersApi } from '../api/customers';
import type { CustomerResponse } from '../types';
import { useDebounce } from '../hooks/useDebounce';
import { Input, Spinner, EmptyState, Badge, Avatar } from '../components/ui';
import { Search, Users } from 'lucide-react';

export function Customers() {
  const [customers, setCustomers] = useState<CustomerResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 400);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    customersApi.list({ query: debouncedSearch, limit: 50, offset: 0 })
      .then(setCustomers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [debouncedSearch]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Customers</h2>
          <p className="text-sm text-slate-500 dark:text-gray-400">Manage and view customer profiles</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <Input 
              placeholder="Search customers..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-10 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-40"><Spinner size="lg" /></div>
        ) : customers.length === 0 ? (
          <EmptyState icon={Users} title="No customers found" description="Try adjusting your search query." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-6">
            {customers.map(c => (
              <div 
                key={c.id} 
                onClick={() => navigate(`/customers/${c.id}`)}
                className="card-surface p-4 cursor-pointer hover:border-brand-400 dark:hover:border-brand-500 transition flex flex-col gap-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <Avatar name={c.full_name} />
                    <div className="min-w-0">
                      <div className="font-semibold text-slate-900 dark:text-white truncate">{c.full_name}</div>
                      <div className="text-xs text-slate-500 dark:text-gray-400 truncate">{c.email}</div>
                    </div>
                  </div>
                  <Badge variant={c.status === 'active' ? 'success' : c.status === 'at_risk' ? 'warning' : 'neutral'}>
                    {c.status.replace('_', ' ')}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-gray-400 mt-2">
                  <div className="truncate">Tier: <span className="font-medium text-slate-700 dark:text-slate-300 capitalize">{c.account_tier}</span></div>
                  {c.company && <div className="truncate">Co: <span className="font-medium text-slate-700 dark:text-slate-300">{c.company}</span></div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { customersApi } from '../api/customers';
import type { CustomerDetailResponse } from '../types';
import { Spinner, Avatar, Badge, Button, Input } from '../components/ui';
import { ArrowLeft, Mail, Phone, MapPin, Building, Calendar } from 'lucide-react';
import { useToast } from '../hooks/useToast';

export function CustomerDetail() {
  const { id } = useParams<{id: string}>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [customer, setCustomer] = useState<CustomerDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'profile' | 'orders' | 'tickets' | 'notes'>('orders');
  const [note, setNote] = useState('');

  useEffect(() => {
    if (!id) return;
    customersApi.get(id).then(setCustomer).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!note.trim() || !id) return;
    try {
      const newNote = await customersApi.addNote(id, note);
      setCustomer(prev => prev ? { ...prev, notes: [newNote, ...prev.notes] } : null);
      setNote('');
      toast.success('Note added');
    } catch (e) {
      toast.error('Failed to add note');
    }
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;
  if (!customer) return <div className="text-center p-10 dark:text-white">Customer not found</div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col md:flex-row md:items-center gap-4 mb-6 shrink-0">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 transition self-start md:self-auto">
          <ArrowLeft size={20} className="text-slate-600 dark:text-gray-400" />
        </button>
        <div className="flex items-center gap-4">
          <Avatar name={customer.full_name} size="lg" className="hidden sm:flex" />
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{customer.full_name}</h2>
              <Badge variant={customer.status === 'active' ? 'success' : 'warning'}>{customer.status.replace('_', ' ')}</Badge>
              <Badge variant="info" className="uppercase">{customer.account_tier}</Badge>
            </div>
            <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">{customer.email}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0 overflow-hidden">
        {/* Sidebar Info */}
        <div className="lg:w-1/3 xl:w-1/4 flex flex-col gap-4 shrink-0 overflow-y-auto scrollbar-thin">
          <div className="card-surface p-5 dark:bg-gray-800 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 uppercase tracking-wider">Contact Info</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                <Mail size={16} className="text-slate-400 shrink-0" />
                <span className="truncate">{customer.email}</span>
              </div>
              {customer.phone && (
                <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                  <Phone size={16} className="text-slate-400 shrink-0" />
                  <span>{customer.phone}</span>
                </div>
              )}
              {customer.company && (
                <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                  <Building size={16} className="text-slate-400 shrink-0" />
                  <span className="truncate">{customer.company}</span>
                </div>
              )}
              {(customer.city || customer.country) && (
                <div className="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-300">
                  <MapPin size={16} className="text-slate-400 shrink-0 mt-0.5" />
                  <span>{[customer.city, customer.country].filter(Boolean).join(', ')}</span>
                </div>
              )}
            </div>
            <Button variant="secondary" className="w-full mt-6">Edit Profile</Button>
          </div>
          
          <div className="card-surface p-5 dark:bg-gray-800 dark:border-gray-700 hidden lg:block">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 uppercase tracking-wider">Account Stats</h3>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-slate-500 dark:text-gray-400">Total Orders</span>
              <span className="font-semibold text-slate-900 dark:text-white">{customer.orders.length}</span>
            </div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-slate-500 dark:text-gray-400">Support Tickets</span>
              <span className="font-semibold text-slate-900 dark:text-white">{customer.tickets.length}</span>
            </div>
            <div className="flex justify-between items-center text-xs text-slate-400 pt-3 border-t border-slate-100 dark:border-gray-700">
              <span className="flex items-center gap-1"><Calendar size={12} /> Joined</span>
              <span>{new Date(customer.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Main Tabs Area */}
        <div className="lg:w-2/3 xl:w-3/4 flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700 overflow-hidden flex-1">
          <div className="flex border-b border-slate-200 dark:border-gray-700 overflow-x-auto scrollbar-thin shrink-0">
            {[
              { id: 'orders', label: `Orders (${customer.orders.length})` },
              { id: 'tickets', label: `Tickets (${customer.tickets.length})` },
              { id: 'notes', label: `Notes (${customer.notes.length})` }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 sm:px-6 py-4 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === tab.id 
                    ? 'border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-400' 
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 hover:border-slate-600'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50 dark:bg-gray-900/50">
            {activeTab === 'notes' && (
              <div className="space-y-6">
                <form onSubmit={handleAddNote} className="card-surface p-4 flex flex-col sm:flex-row gap-3 dark:bg-gray-800 dark:border-gray-700">
                  <Input placeholder="Add a note about this customer..." value={note} onChange={e => setNote(e.target.value)} className="flex-1 dark:bg-gray-900 dark:border-gray-700 dark:text-white" />
                  <Button type="submit" disabled={!note.trim()} className="sm:w-auto w-full">Add Note</Button>
                </form>
                <div className="space-y-4">
                  {customer.notes.map(n => (
                    <div key={n.id} className="card-surface p-4 flex gap-4 dark:bg-gray-800 dark:border-gray-700">
                      <Avatar name={n.author} size="sm" className="mt-1 shrink-0 hidden sm:flex" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-sm text-slate-900 dark:text-white truncate">{n.author}</span>
                          <span className="text-xs text-slate-500 dark:text-gray-400 shrink-0">{new Date(n.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-sm text-slate-700 dark:text-slate-300 break-words">{n.body}</p>
                      </div>
                    </div>
                  ))}
                  {customer.notes.length === 0 && <div className="text-center p-8 text-slate-400 text-sm">No notes yet.</div>}
                </div>
              </div>
            )}
            
            {activeTab === 'orders' && (
              <div className="space-y-4">
                {customer.orders.map(o => (
                  <div key={o.id} className="card-surface p-4 flex flex-col sm:flex-row justify-between sm:items-center gap-4 dark:bg-gray-800 dark:border-gray-700">
                    <div>
                      <div className="font-semibold text-sm text-slate-900 dark:text-white mb-1">{o.order_number}</div>
                      <div className="text-xs text-slate-500 dark:text-gray-400">{new Date(o.placed_at).toLocaleDateString()} • {o.items.length} items</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="font-medium text-slate-900 dark:text-white">{o.currency} {o.total_amount}</div>
                      <Badge variant={o.status === 'delivered' ? 'success' : o.status === 'cancelled' ? 'danger' : 'neutral'}>{o.status}</Badge>
                    </div>
                  </div>
                ))}
                {customer.orders.length === 0 && <div className="text-center p-8 text-slate-400 dark:text-gray-500 text-sm">No orders found.</div>}
              </div>
            )}

            {activeTab === 'tickets' && (
              <div className="space-y-4">
                {customer.tickets.map(t => (
                  <div key={t.id} onClick={() => navigate(`/tickets/${t.id}`)} className="card-surface p-4 cursor-pointer hover:border-brand-400 dark:hover:border-brand-500 transition dark:bg-gray-800 dark:border-gray-700">
                    <div className="flex justify-between mb-2 gap-2">
                      <span className="font-semibold text-sm text-brand-600 dark:text-brand-400 truncate">#{t.ticket_number}</span>
                      <Badge variant="neutral" className="shrink-0">{t.status.replace('_', ' ')}</Badge>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-200 line-clamp-2">{t.subject}</p>
                    <div className="text-xs text-slate-500 dark:text-gray-400 mt-2">{new Date(t.created_at).toLocaleDateString()} • {t.channel}</div>
                  </div>
                ))}
                {customer.tickets.length === 0 && <div className="text-center p-8 text-slate-400 dark:text-gray-500 text-sm">No tickets found.</div>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

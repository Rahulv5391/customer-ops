import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/analytics';
import type { AnalyticsSummary, TopIssueCategory } from '../types';
import { Spinner } from '../components/ui';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { CheckCircle2, Clock, Star, ShieldCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const PIE_COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [topCategories, setTopCategories] = useState<TopIssueCategory[]>([]);
  const [resolvedToday, setResolvedToday] = useState(0);
  const [loading, setLoading] = useState(true);
  const { agent } = useAuth();

  useEffect(() => {
    Promise.all([
      analyticsApi.summary(),
      analyticsApi.topIssueCategories(),
      analyticsApi.ticketsResolvedToday()
    ]).then(([sum, cats, resToday]) => {
      setSummary(sum);
      setTopCategories(cats);
      setResolvedToday(resToday.count);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading || !summary) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  const stats = [
    { title: 'Resolved Today', value: resolvedToday, icon: CheckCircle2, iconColor: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
    { title: 'Avg Resolution', value: summary.avg_resolution_time_hours ? `${summary.avg_resolution_time_hours.toFixed(1)}h` : 'N/A', icon: Clock, iconColor: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30' },
    { title: 'CSAT Average', value: summary.csat_average ? `${summary.csat_average.toFixed(1)}/5` : 'N/A', icon: Star, iconColor: 'text-amber-500 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30' },
    { title: 'AI Deflection', value: summary.deflection_rate ? `${summary.deflection_rate.toFixed(1)}%` : 'N/A', icon: ShieldCheck, iconColor: 'text-brand-600 dark:text-brand-400', bg: 'bg-brand-100 dark:bg-brand-900/30' },
  ];

  const chartData = summary.ticket_volume_7d.map(d => ({
    ...d,
    day: new Date(d.date).toLocaleDateString(undefined, { weekday: 'short' })
  }));

  // Recharts needs a custom tooltip container to respect dark mode correctly without ugly hacks
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-slate-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="text-sm font-semibold text-slate-900 dark:text-white mb-1">{label}</p>
          <p className="text-sm text-brand-600 dark:text-brand-400 font-medium">
            {payload[0].value} Tickets
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="mb-6 shrink-0">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {agent?.full_name.split(' ')[0]}
        </h2>
        <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Here is what's happening with your support operations today.</p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={i} className="card-surface p-5 dark:bg-gray-800 dark:border-gray-700 transition-transform hover:-translate-y-1 duration-200">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${s.bg}`}>
                    <Icon size={24} className={s.iconColor} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">{s.title}</p>
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-0.5">{s.value}</h3>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-6">
          <div className="card-surface p-5 lg:col-span-2 dark:bg-gray-800 dark:border-gray-700 flex flex-col min-h-[350px]">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-6 uppercase tracking-wider">Ticket Volume (Last 7 Days)</h3>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#4F46E5" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#64748b" opacity={0.15} />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="count" stroke="#4F46E5" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card-surface p-5 dark:bg-gray-800 dark:border-gray-700 flex flex-col min-h-[350px]">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-2 uppercase tracking-wider">Top Categories</h3>
            <div className="flex-1 relative">
              {topCategories.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-400">No data available</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={topCategories}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="count"
                      nameKey="category"
                    >
                      {topCategories.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', backgroundColor: 'var(--tw-colors-white, #fff)' }}
                      formatter={(value: any, name: any) => [value, String(name).charAt(0).toUpperCase() + String(name).slice(1).replace('_', ' ')]}
                    />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36} 
                      iconType="circle" 
                      formatter={(value) => <span className="text-sm text-slate-600 dark:text-gray-300 capitalize">{value.replace('_', ' ')}</span>} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { analyticsApi } from '../api/analytics';
import type { AnalyticsSummary, TopIssueCategory } from '../types';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { CheckCircle2, Clock, Star, ShieldCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useCountUp } from '../hooks/useCountUp';

const PIE_COLORS = ['#147F72', '#F59E0B', '#E1483A', '#7C6FE0', '#98917F'];
const BRAND = '#147F72';

function AnimatedNumber({ value, format }: { value: number; format: (n: number) => string }) {
  const animated = useCountUp(value);
  return <>{format(animated)}</>;
}

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

  if (loading || !summary) {
    return (
      <div className="h-full flex flex-col gap-6">
        <div className="space-y-2">
          <div className="skeleton h-7 w-64" />
          <div className="skeleton h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-24" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="skeleton h-80 lg:col-span-2" />
          <div className="skeleton h-80" />
        </div>
      </div>
    );
  }

  const stats = [
    {
      title: 'Resolved Today', icon: CheckCircle2,
      iconColor: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30',
      value: resolvedToday, format: (n: number) => String(Math.round(n)),
    },
    {
      title: 'Avg Resolution', icon: Clock,
      iconColor: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30',
      value: summary.avg_resolution_time_hours, format: (n: number) => `${n.toFixed(1)}h`,
    },
    {
      title: 'CSAT Average', icon: Star,
      iconColor: 'text-amber-500 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30',
      value: summary.csat_average, format: (n: number) => `${n.toFixed(1)}/5`,
    },
    {
      title: 'AI Deflection', icon: ShieldCheck,
      iconColor: 'text-brand-600 dark:text-brand-400', bg: 'bg-brand-100 dark:bg-brand-900/30',
      value: summary.deflection_rate ? summary.deflection_rate * 100 : summary.deflection_rate, format: (n: number) => `${n.toFixed(1)}%`,
    },
  ];

  const chartData = summary.ticket_volume_7d.map(d => ({
    ...d,
    day: new Date(d.date).toLocaleDateString(undefined, { weekday: 'short' })
  }));

  // Recharts needs a custom tooltip container to respect dark mode correctly without ugly hacks
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-slate-200 dark:border-gray-700 rounded-lg" style={{ boxShadow: 'var(--shadow-pop)' }}>
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
      <div className="mb-6 shrink-0 animate-fade-in-up">
        <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">
          Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {agent?.full_name.split(' ')[0]}
        </h2>
        <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Here is what's happening with your support operations today.</p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6 stagger">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={i} className="card-interactive p-5">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${s.bg}`}>
                    <Icon size={24} className={s.iconColor} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">{s.title}</p>
                    <h3 className="font-display text-2xl font-bold text-slate-900 dark:text-white mt-0.5 tabular-nums">
                      {s.value == null ? 'N/A' : <AnimatedNumber value={s.value} format={s.format} />}
                    </h3>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-6">
          <div className="card-surface p-5 lg:col-span-2 flex flex-col min-h-[350px] animate-fade-in-up" style={{ animationDelay: '120ms' }}>
            <h3 className="font-display text-base font-semibold text-slate-900 dark:text-white mb-6 uppercase tracking-wider">Ticket Volume (Last 7 Days)</h3>
            <div className="flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={BRAND} stopOpacity={0.32}/>
                      <stop offset="95%" stopColor={BRAND} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#7e7666" opacity={0.15} />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#7e7666' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#7e7666' }} allowDecimals={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="count" stroke={BRAND} strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" animationDuration={900} animationEasing="ease-out" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card-surface p-5 flex flex-col min-h-[350px] animate-fade-in-up" style={{ animationDelay: '200ms' }}>
            <h3 className="font-display text-base font-semibold text-slate-900 dark:text-white mb-2 uppercase tracking-wider">Top Categories</h3>
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
                      animationDuration={900}
                      animationEasing="ease-out"
                    >
                      {topCategories.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-pop)', backgroundColor: 'var(--tw-colors-white, #fff)' }}
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

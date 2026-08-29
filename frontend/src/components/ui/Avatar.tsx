import { useMemo } from 'react';

const COLORS = [
  'bg-violet-500', 'bg-indigo-500', 'bg-blue-500', 'bg-cyan-500',
  'bg-teal-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500',
  'bg-pink-500', 'bg-purple-500',
];

function getColor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return COLORS[Math.abs(hash) % COLORS.length];
}

function getInitials(name: string) {
  return name.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase();
}

const sizeClasses = { sm: 'w-7 h-7 text-xs', md: 'w-9 h-9 text-sm', lg: 'w-12 h-12 text-base' };

interface AvatarProps { name: string; size?: 'sm' | 'md' | 'lg'; className?: string; }

export function Avatar({ name, size = 'md', className = '' }: AvatarProps) {
  const color = useMemo(() => getColor(name), [name]);
  const initials = useMemo(() => getInitials(name), [name]);
  return (
    <div className={`${sizeClasses[size]} ${color} rounded-full flex items-center justify-center font-semibold text-white shrink-0 ${className}`}>
      {initials}
    </div>
  );
}

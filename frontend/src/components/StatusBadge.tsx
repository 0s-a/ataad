import React from 'react';
import { cn } from '../lib/utils';
import { AssetStatus } from '../types';

interface StatusBadgeProps {
  status: AssetStatus;
  label?: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, className }) => {
  let badgeClasses = '';
  let dotColor = '';
  let defaultLabel = '';

  switch (status) {
    case 'active':
    case 'installed':
      badgeClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200/80 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/40';
      dotColor = 'bg-emerald-500';
      defaultLabel = status === 'installed' ? 'مركّب بالجهاز' : 'نشط';
      break;

    case 'in_storage':
      badgeClasses = 'bg-sky-50 text-sky-700 border-sky-200/80 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-800/40';
      dotColor = 'bg-sky-500';
      defaultLabel = 'في الدرج';
      break;

    case 'with_person':
      badgeClasses = 'bg-amber-50 text-amber-700 border-amber-200/80 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/40';
      dotColor = 'bg-amber-500';
      defaultLabel = 'في عهدة شخص';
      break;

    case 'faulty':
      badgeClasses = 'bg-rose-50 text-rose-700 border-rose-200/80 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/40';
      dotColor = 'bg-rose-500';
      defaultLabel = 'تالف';
      break;

    case 'sold':
    default:
      badgeClasses = 'bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800/50 dark:text-zinc-400 dark:border-zinc-700';
      dotColor = 'bg-zinc-400';
      defaultLabel = 'مستبعد / مباع';
      break;
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors',
        badgeClasses,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full animate-pulse', dotColor)} />
      {label || defaultLabel}
    </span>
  );
};

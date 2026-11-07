import React from 'react';
import { Search, ChevronLeft, Plus } from 'lucide-react';
import { Button } from './Button';

interface HeaderProps {
  breadcrumbs: string[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
  searchPlaceholder?: string;
  primaryActionLabel?: string;
  onPrimaryAction?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  breadcrumbs,
  searchQuery,
  onSearchChange,
  searchPlaceholder = 'بحث بالسيريال، الاسم، أو الموديل...',
  primaryActionLabel,
  onPrimaryAction,
}) => {
  return (
    <header className="h-16 px-6 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between gap-4 flex-shrink-0">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
        <span className="font-medium text-zinc-900 dark:text-zinc-100">عَتاد</span>
        {breadcrumbs.map((crumb, idx) => (
          <React.Fragment key={idx}>
            <ChevronLeft className="w-3.5 h-3.5 text-zinc-400 rtl:rotate-0" />
            <span
              className={
                idx === breadcrumbs.length - 1
                  ? 'font-medium text-zinc-900 dark:text-zinc-100'
                  : ''
              }
            >
              {crumb}
            </span>
          </React.Fragment>
        ))}
      </nav>

      {/* Search and Action */}
      <div className="flex items-center gap-3 flex-1 max-w-md justify-end">
        <div className="relative w-full max-w-xs">
          <Search className="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-3 pr-8 py-1.5 text-xs bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700/80 rounded-md text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-zinc-400 dark:focus:ring-zinc-500 focus:bg-white dark:focus:bg-zinc-800 transition-all font-sans"
          />
        </div>

        {primaryActionLabel && onPrimaryAction && (
          <Button size="sm" variant="primary" onClick={onPrimaryAction} className="whitespace-nowrap">
            <Plus className="w-3.5 h-3.5" />
            <span>{primaryActionLabel}</span>
          </Button>
        )}
      </div>
    </header>
  );
};

import React from 'react';
import { 
  Laptop, 
  Archive, 
  Users, 
  BookOpen, 
  Upload, 
  Moon, 
  Sun,
  Server
} from 'lucide-react';
import { cn } from '../lib/utils';

export type NavTab = 'devices' | 'drawer' | 'custody' | 'catalog';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  onOpenIngest: () => void;
  counts: {
    devices: number;
    drawer: number;
    custody: number;
  };
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  onOpenIngest,
  counts,
  isDark,
  onToggleTheme,
}) => {
  const navItems = [
    {
      id: 'devices' as NavTab,
      label: 'الأجهزة',
      icon: Laptop,
      badge: counts.devices,
    },
    {
      id: 'drawer' as NavTab,
      label: 'درج القطع',
      icon: Archive,
      badge: counts.drawer,
    },
    {
      id: 'custody' as NavTab,
      label: 'العُهد',
      icon: Users,
      badge: counts.custody,
    },
    {
      id: 'catalog' as NavTab,
      label: 'الكتالوج',
      icon: BookOpen,
      badge: undefined,
    },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 flex flex-col justify-between select-none">
      {/* Brand Header */}
      <div>
        <div className="h-16 px-5 flex items-center justify-between border-b border-zinc-200/80 dark:border-zinc-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 shadow-sm">
              <Server className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-zinc-900 dark:text-zinc-100">
                عَتاد
              </span>
              <span className="mr-1 text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                v3.0
              </span>
            </div>
          </div>
        </div>

        {/* Action Button: Ingest CPU-Z */}
        <div className="p-3">
          <button
            onClick={onOpenIngest}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-white bg-zinc-900 hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 rounded-md transition-all shadow-xs"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>استيراد تقرير CPU-Z</span>
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="px-3 py-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={cn(
                  'w-full flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-zinc-100 text-zinc-950 dark:bg-zinc-800/80 dark:text-zinc-50'
                    : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:text-zinc-200 dark:hover:bg-zinc-800/40'
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={cn('w-4 h-4', isActive ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-400')} />
                  <span>{item.label}</span>
                </div>
                {typeof item.badge === 'number' && (
                  <span
                    className={cn(
                      'text-xs font-mono px-2 py-0.5 rounded-full',
                      isActive
                        ? 'bg-zinc-200 dark:bg-zinc-700 text-zinc-800 dark:text-zinc-200'
                        : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer / Theme toggle & system state */}
      <div className="p-3 border-t border-zinc-200/80 dark:border-zinc-800 flex items-center justify-between">
        <button
          onClick={onToggleTheme}
          className="flex items-center gap-2 text-xs font-medium text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 p-1.5 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          title="تبديل المظهر"
        >
          {isDark ? (
            <>
              <Sun className="w-4 h-4 text-amber-500" />
              <span>الوضع الفاتح</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 text-zinc-600" />
              <span>الوضع الداكن</span>
            </>
          )}
        </button>

        <span className="text-[11px] text-zinc-400 font-mono">
          Medusa UI RTL
        </span>
      </div>
    </aside>
  );
};

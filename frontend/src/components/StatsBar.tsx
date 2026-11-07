import React from 'react';
import { Laptop, Cpu, HardDrive, Archive } from 'lucide-react';
import { StatsSummary } from '../types';

interface StatsBarProps {
  stats: StatsSummary;
  className?: string;
}

export const StatsBar: React.FC<StatsBarProps> = ({ stats, className }) => {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-subtle overflow-hidden ${className || ''}`}>
      {/* 1. الأجهزة النشطة */}
      <div className="flex items-center gap-3.5 p-3.5 border-b md:border-b-0 border-l border-zinc-100 dark:border-zinc-800/80">
        <div className="p-2 rounded-md bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          <Laptop className="w-4 h-4" />
        </div>
        <div>
          <div className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            {stats.active_devices_count} <span className="text-xs font-normal text-zinc-500">أجهزة</span>
          </div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400">
            أجهزة مسجلة ونشطة
          </div>
        </div>
      </div>

      {/* 2. إجمالي الرامات */}
      <div className="flex items-center gap-3.5 p-3.5 border-b md:border-b-0 md:border-l border-zinc-100 dark:border-zinc-800/80">
        <div className="p-2 rounded-md bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          <Cpu className="w-4 h-4" />
        </div>
        <div>
          <div className="text-base font-semibold text-zinc-900 dark:text-zinc-100 font-mono">
            {stats.total_ram_gb} <span className="text-xs font-sans font-normal text-zinc-500">GB</span>
          </div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400">
            إجمالي الذاكرة المركبة
          </div>
        </div>
      </div>

      {/* 3. إجمالي التخزين */}
      <div className="flex items-center gap-3.5 p-3.5 border-l border-zinc-100 dark:border-zinc-800/80">
        <div className="p-2 rounded-md bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          <HardDrive className="w-4 h-4" />
        </div>
        <div>
          <div className="text-base font-semibold text-zinc-900 dark:text-zinc-100 font-mono">
            {stats.total_storage_tb} <span className="text-xs font-sans font-normal text-zinc-500">TB</span>
          </div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400">
            إجمالي وسائط التخزين
          </div>
        </div>
      </div>

      {/* 4. القطع في الدرج */}
      <div className="flex items-center gap-3.5 p-3.5">
        <div className="p-2 rounded-md bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          <Archive className="w-4 h-4" />
        </div>
        <div>
          <div className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            {stats.drawer_parts_count} <span className="text-xs font-normal text-zinc-500">قطع</span>
          </div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400">
            مخزنة في درج الغيار
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { BookOpen, Search, Layers, Cpu, HardDrive, Laptop } from 'lucide-react';
import { AssetModel } from '../types';

interface CatalogPageProps {
  catalogModels: AssetModel[];
  searchQuery: string;
}

export const CatalogPage: React.FC<CatalogPageProps> = ({
  catalogModels,
  searchQuery,
}) => {
  const filteredModels = catalogModels.filter(m => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      m.name.toLowerCase().includes(q) ||
      (m.model_number && m.model_number.toLowerCase().includes(q)) ||
      (m.manufacturer_name && m.manufacturer_name.toLowerCase().includes(q)) ||
      (m.type_label_ar && m.type_label_ar.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-base font-semibold text-zinc-950 dark:text-zinc-50">
          كتالوج الموديلات المرجعي ({catalogModels.length})
        </h1>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          القاموس الموحد لمواصفات الأجهزة والقطع المصنعية المسجلة بالنظام
        </p>
      </div>

      {/* Grid of Catalog Models */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredModels.map((model) => (
          <div
            key={model.id}
            className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 shadow-subtle space-y-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                  {model.manufacturer_name || 'عام'}
                </span>
                <h3 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 mt-2">
                  {model.name}
                </h3>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200/80 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300">
                {model.type_label_ar || 'قطعة'}
              </span>
            </div>

            {model.model_number && (
              <div className="font-mono text-[11px] text-zinc-500">
                رقم الموديل: {model.model_number}
              </div>
            )}

            {model.notes && (
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                {model.notes}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

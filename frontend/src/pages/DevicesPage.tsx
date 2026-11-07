import React, { useState } from 'react';
import { 
  Laptop, 
  Server, 
  Monitor, 
  ChevronLeft, 
  MoreHorizontal, 
  Cpu, 
  Layers, 
  Plus,
  Search,
  ExternalLink
} from 'lucide-react';
import { DeviceWithDetails, Asset } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { DeviceDetailDrawer } from '../components/DeviceDetailDrawer';
import { Button } from '../components/Button';
import { formatRam, formatStorage, formatRelativeTime } from '../lib/utils';

interface DevicesPageProps {
  devices: DeviceWithDetails[];
  searchQuery: string;
  onSelectDevice: (device: DeviceWithDetails) => void;
  selectedDevice: DeviceWithDetails | null;
  isDrawerOpen: boolean;
  onCloseDrawer: () => void;
  onUnmountPart: (partId: string, storageBox: string) => Promise<void>;
  onOpenNewDeviceModal?: () => void;
}

export const DevicesPage: React.FC<DevicesPageProps> = ({
  devices,
  searchQuery,
  onSelectDevice,
  selectedDevice,
  isDrawerOpen,
  onCloseDrawer,
  onUnmountPart,
  onOpenNewDeviceModal,
}) => {
  const getChassisIcon = (subtype?: string) => {
    switch (subtype) {
      case 'server_rack':
        return <Server className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />;
      case 'desktop_tower':
      case 'sff':
      case 'mini_pc':
        return <Monitor className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />;
      case 'laptop':
      default:
        return <Laptop className="w-4 h-4 text-zinc-600 dark:text-zinc-400" />;
    }
  };

  const getChassisLabel = (subtype?: string) => {
    switch (subtype) {
      case 'server_rack':
        return 'خادم / سيرفر';
      case 'desktop_tower':
        return 'مكتبي برج';
      case 'sff':
      case 'mini_pc':
        return 'مكتبي صغير';
      case 'laptop':
      default:
        return 'لابتوب محمول';
    }
  };

  const filteredDevices = devices.filter(d => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      d.name.toLowerCase().includes(q) ||
      (d.serial_number && d.serial_number.toLowerCase().includes(q)) ||
      (d.profile?.cpu_model && d.profile.cpu_model.toLowerCase().includes(q)) ||
      (d.assigned_person_name && d.assigned_person_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-4">
      {/* Table Action Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-zinc-950 dark:text-zinc-50">
            الأجهزة المجمعة ({filteredDevices.length})
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            استعراض كافة الحواسيب والسيرفرات، مواصفاتها وحالة تجميعها
          </p>
        </div>

        {onOpenNewDeviceModal && (
          <Button size="sm" variant="primary" onClick={onOpenNewDeviceModal}>
            <Plus className="w-3.5 h-3.5" />
            <span>جهاز جديد</span>
          </Button>
        )}
      </div>

      {/* Medusa Data Grid */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-subtle overflow-hidden">
        {filteredDevices.length === 0 ? (
          <div className="p-12 text-center text-zinc-500 text-sm">
            <Laptop className="w-10 h-10 mx-auto text-zinc-300 dark:text-zinc-700 mb-3" />
            <p>لا توجد أجهزة مطابقة لخيارات البحث</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/60 text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider select-none">
                  <th className="py-3 px-4">اسم الجهاز والموديل</th>
                  <th className="py-3 px-4">النوع</th>
                  <th className="py-3 px-4">المواصفات الأساسية</th>
                  <th className="py-3 px-4">الحالة والعهدة</th>
                  <th className="py-3 px-4">آخر فحص</th>
                  <th className="py-3 px-4 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs text-zinc-900 dark:text-zinc-100">
                {filteredDevices.map((device) => {
                  const ramMb = device.profile?.total_ram_mb || device.specs?.ram_mb || 0;
                  const storageGb = device.profile?.total_storage_gb || device.specs?.storage_gb || 0;
                  const cpuBrief = device.profile?.cpu_model?.split('@')[0] || device.specs?.cpu || 'غير محدد';
                  const isSelected = selectedDevice?.id === device.id && isDrawerOpen;

                  return (
                    <tr
                      key={device.id}
                      onClick={() => onSelectDevice(device)}
                      className={`cursor-pointer transition-colors group ${
                        isSelected 
                          ? 'bg-zinc-100/80 dark:bg-zinc-800/60' 
                          : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                      }`}
                    >
                      {/* Name & Serial */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-md bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center flex-shrink-0 group-hover:bg-zinc-200 dark:group-hover:bg-zinc-700 transition-colors">
                            {getChassisIcon(device.profile?.chassis_subtype || device.specs?.chassis)}
                          </div>
                          <div>
                            <div className="font-medium text-zinc-950 dark:text-zinc-50 flex items-center gap-1.5">
                              <span>{device.name}</span>
                            </div>
                            <div className="font-mono text-[11px] text-zinc-400 mt-0.5">
                              {device.serial_number ? `SN: ${device.serial_number}` : 'بدون سيريال'}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Type Badge */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                          {getChassisLabel(device.profile?.chassis_subtype || device.specs?.chassis)}
                        </span>
                      </td>

                      {/* Specifications Summary */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="text-zinc-800 dark:text-zinc-200 truncate max-w-xs" title={device.profile?.cpu_model || ''}>
                          {cpuBrief}
                        </div>
                        <div className="text-[11px] text-zinc-400 mt-0.5 flex items-center gap-2">
                          <span>{formatRam(ramMb)} RAM</span>
                          <span>•</span>
                          <span>{formatStorage(storageGb)}</span>
                          {device.components && (
                            <>
                              <span>•</span>
                              <span>{device.components.length} قطع</span>
                            </>
                          )}
                        </div>
                      </td>

                      {/* Status / Custody */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {device.status === 'with_person' ? (
                          <StatusBadge 
                            status="with_person" 
                            label={`عهدة: ${device.assigned_person_name || 'شخص'}`} 
                          />
                        ) : (
                          <StatusBadge 
                            status={device.status} 
                            label={device.status === 'active' ? 'معي شخصياً' : undefined}
                          />
                        )}
                      </td>

                      {/* Last scan */}
                      <td className="py-3.5 px-4 whitespace-nowrap text-zinc-500 font-mono text-[11px]">
                        {formatRelativeTime(device.profile?.last_scanned_at || device.last_seen_at)}
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-center whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectDevice(device);
                          }}
                          className="p-1.5 rounded text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                          title="عرض شجرة العتاد والتفاصيل"
                        >
                          <ChevronLeft className="w-4 h-4 rtl:rotate-0" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Slide-over Drawer for Device Details */}
      <DeviceDetailDrawer
        device={selectedDevice}
        isOpen={isDrawerOpen}
        onClose={onCloseDrawer}
        onUnmountPart={onUnmountPart}
      />
    </div>
  );
};

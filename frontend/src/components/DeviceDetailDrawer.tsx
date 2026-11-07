import React, { useState } from 'react';
import { 
  Cpu, 
  HardDrive, 
  CircuitBoard, 
  Monitor, 
  Layers, 
  Clock, 
  Box, 
  Wrench,
  CheckCircle2,
  Trash2
} from 'lucide-react';
import { SlideOverDrawer } from './SlideOverDrawer';
import { StatusBadge } from './StatusBadge';
import { Button } from './Button';
import { Modal } from './Modal';
import { DeviceWithDetails, Asset } from '../types';
import { formatRam, formatStorage, formatRelativeTime } from '../lib/utils';

interface DeviceDetailDrawerProps {
  device: DeviceWithDetails | null;
  isOpen: boolean;
  onClose: () => void;
  onUnmountPart: (partId: string, storageBox: string) => Promise<void>;
}

export const DeviceDetailDrawer: React.FC<DeviceDetailDrawerProps> = ({
  device,
  isOpen,
  onClose,
  onUnmountPart,
}) => {
  const [activeTab, setActiveTab] = useState<'assembly' | 'specs' | 'history'>('assembly');
  
  // Unmount modal state
  const [unmountPartModal, setUnmountPartModal] = useState<Asset | null>(null);
  const [storageBoxInput, setStorageBoxInput] = useState('درج 1 - علبة A');
  const [isUnmounting, setIsUnmounting] = useState(false);

  if (!device) return null;

  const profile = device.profile;
  const components = device.components || [];

  const ramComponents = components.filter(c => c.component_type_slug === 'RAM');
  const storageComponents = components.filter(c => c.component_type_slug === 'STORAGE');
  const gpuComponents = components.filter(c => c.component_type_slug === 'GPU');
  const otherComponents = components.filter(c => !['RAM', 'STORAGE', 'GPU'].includes(c.component_type_slug || ''));

  const handleConfirmUnmount = async () => {
    if (!unmountPartModal) return;
    setIsUnmounting(true);
    try {
      await onUnmountPart(unmountPartModal.id, storageBoxInput);
      setUnmountPartModal(null);
    } finally {
      setIsUnmounting(false);
    }
  };

  return (
    <>
      <SlideOverDrawer
        isOpen={isOpen}
        onClose={onClose}
        title={
          <div className="flex items-center gap-2">
            <span>{device.name}</span>
            <StatusBadge status={device.status} />
          </div>
        }
        subtitle={
          <div className="flex items-center gap-2 font-mono text-zinc-500">
            <span>سيريال: {device.serial_number || 'غير متوفر'}</span>
            <span>•</span>
            <span>آخر فحص: {formatRelativeTime(profile?.last_scanned_at || device.last_seen_at)}</span>
          </div>
        }
      >
        {/* Navigation Tabs */}
        <div className="flex border-b border-zinc-200 dark:border-zinc-800 -mx-6 px-6 -mt-2">
          <button
            onClick={() => setActiveTab('assembly')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'assembly'
                ? 'border-zinc-900 text-zinc-950 dark:border-zinc-100 dark:text-zinc-50'
                : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
            }`}
          >
            العتاد المركّب ({components.length})
          </button>
          <button
            onClick={() => setActiveTab('specs')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'specs'
                ? 'border-zinc-900 text-zinc-950 dark:border-zinc-100 dark:text-zinc-50'
                : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
            }`}
          >
            اللوحة والمواصفات المعمارية
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`pb-3 px-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'history'
                ? 'border-zinc-900 text-zinc-950 dark:border-zinc-100 dark:text-zinc-50'
                : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
            }`}
          >
            سجل الفحوصات والحركات ({device.history?.length || 0})
          </button>
        </div>

        {/* ======================================================== */}
        {/* TAB 1: INSTALLED HARDWARE ASSEMBLY                       */}
        {/* ======================================================== */}
        {activeTab === 'assembly' && (
          <div className="space-y-6">
            {/* Quick Summary Strip */}
            <div className="grid grid-cols-3 gap-2 p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg border border-zinc-200/80 dark:border-zinc-800 text-xs">
              <div>
                <span className="text-zinc-400 block mb-0.5">إجمالي الرام:</span>
                <span className="font-semibold font-mono text-zinc-900 dark:text-zinc-100">
                  {formatRam(profile?.total_ram_mb || device.specs?.ram_mb || 0)}
                </span>
              </div>
              <div>
                <span className="text-zinc-400 block mb-0.5">إجمالي التخزين:</span>
                <span className="font-semibold font-mono text-zinc-900 dark:text-zinc-100">
                  {formatStorage(profile?.total_storage_gb || device.specs?.storage_gb || 0)}
                </span>
              </div>
              <div>
                <span className="text-zinc-400 block mb-0.5">المعالج:</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-100 truncate block" title={profile?.cpu_model}>
                  {profile?.cpu_model?.split('@')[0] || device.specs?.cpu || 'غير محدد'}
                </span>
              </div>
            </div>

            {/* RAM Section */}
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-xs">
                    🧠
                  </div>
                  <h3 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 uppercase tracking-wider">
                    شرائح الذاكرة (RAM) — {ramComponents.length} من أصل {profile?.ram_slots_count || 2} منافذ
                  </h3>
                </div>
              </div>

              {ramComponents.length === 0 ? (
                <div className="p-4 border border-dashed border-zinc-200 dark:border-zinc-800 rounded-lg text-center text-xs text-zinc-400">
                  لا توجد شرائح رام مسجلة حالياً
                </div>
              ) : (
                <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg divide-y divide-zinc-100 dark:divide-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
                  {ramComponents.map((ram) => (
                    <div key={ram.id} className="p-3.5 flex items-center justify-between gap-3 hover:bg-zinc-50/60 dark:hover:bg-zinc-800/40 transition-colors">
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-xs text-zinc-900 dark:text-zinc-100 truncate">
                            {ram.name}
                          </span>
                          <span className="text-[11px] px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-mono">
                            {ram.slot_or_bus || 'DIMM'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-zinc-500 font-mono">
                          <span>{formatRam(ram.specs?.capacity_mb || 0)}</span>
                          <span>•</span>
                          <span>{ram.specs?.speed_mhz || '1600'} MHz</span>
                          {ram.serial_number && (
                            <>
                              <span>•</span>
                              <span>SN: {ram.serial_number}</span>
                            </>
                          )}
                        </div>
                      </div>

                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setUnmountPartModal(ram)}
                        className="text-xs text-zinc-600 hover:text-zinc-900 dark:text-zinc-300 flex-shrink-0"
                      >
                        <Wrench className="w-3 h-3 text-zinc-400" />
                        <span>فك إلى الدرج</span>
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Storage Section */}
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-xs">
                    💾
                  </div>
                  <h3 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 uppercase tracking-wider">
                    وسائط التخزين (Storage Drives) — {storageComponents.length} أقراص
                  </h3>
                </div>
              </div>

              {storageComponents.length === 0 ? (
                <div className="p-4 border border-dashed border-zinc-200 dark:border-zinc-800 rounded-lg text-center text-xs text-zinc-400">
                  لا توجد أقراص تخزين مسجلة
                </div>
              ) : (
                <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg divide-y divide-zinc-100 dark:divide-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
                  {storageComponents.map((disk) => (
                    <div key={disk.id} className="p-3.5 flex items-center justify-between gap-3 hover:bg-zinc-50/60 dark:hover:bg-zinc-800/40 transition-colors">
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-xs text-zinc-900 dark:text-zinc-100 truncate">
                            {disk.name}
                          </span>
                          <span className="text-[11px] px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-mono">
                            {disk.slot_or_bus || 'SATA'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-zinc-500 font-mono">
                          <span>{formatStorage(disk.specs?.capacity_gb || 0)}</span>
                          <span>•</span>
                          <span>{disk.specs?.interface || 'SATA'}</span>
                          {disk.serial_number && (
                            <>
                              <span>•</span>
                              <span>SN: {disk.serial_number}</span>
                            </>
                          )}
                        </div>
                      </div>

                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setUnmountPartModal(disk)}
                        className="text-xs text-zinc-600 hover:text-zinc-900 dark:text-zinc-300 flex-shrink-0"
                      >
                        <Wrench className="w-3 h-3 text-zinc-400" />
                        <span>فك إلى الدرج</span>
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Graphics / GPU Section */}
            {gpuComponents.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2.5">
                  <div className="w-5 h-5 rounded bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-xs">
                    🎮
                  </div>
                  <h3 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 uppercase tracking-wider">
                    كروت الشاشة والمعالجة الرسومية
                  </h3>
                </div>
                <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg divide-y divide-zinc-100 dark:divide-zinc-800 bg-white dark:bg-zinc-900 overflow-hidden">
                  {gpuComponents.map((gpu) => (
                    <div key={gpu.id} className="p-3.5 flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium text-xs text-zinc-900 dark:text-zinc-100">
                          {gpu.name}
                        </div>
                        <div className="text-[11px] text-zinc-500 font-mono mt-0.5">
                          {gpu.specs?.is_integrated ? 'مدمج في المعالج (Integrated)' : 'كرت منفصل (Discrete)'}
                          {gpu.specs?.vram_mb ? ` • ${formatRam(gpu.specs.vram_mb)} VRAM` : ''}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 2: DETAILED SPECS GRID                               */}
        {/* ======================================================== */}
        {activeTab === 'specs' && (
          <div className="space-y-6">
            {/* Motherboard & Platform Grid */}
            <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden bg-white dark:bg-zinc-900">
              <div className="px-4 py-2.5 bg-zinc-50 dark:bg-zinc-800/60 border-b border-zinc-200 dark:border-zinc-800 text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <CircuitBoard className="w-4 h-4 text-zinc-500" />
                <span>اللوحة الأم والبيوس (Motherboard & BIOS)</span>
              </div>
              <div className="grid grid-cols-2 text-xs divide-x divide-y divide-zinc-100 dark:divide-zinc-800">
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">الشركة المصنعة:</span>
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">{profile?.motherboard_vendor || 'Dell Inc.'}</span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">موديل اللوحة الدقيق:</span>
                  <span className="font-mono font-medium text-zinc-900 dark:text-zinc-100">{profile?.motherboard_model || '0K9GNV'}</span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">شريحة اللوحة (Chipset):</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">{profile?.chipset || 'Intel Haswell QM87'}</span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">إصدار وتاريخ البيوس:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.bios_version || 'A24'} ({profile?.bios_date || '05/21/2019'})
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">الحد الأقصى للذاكرة:</span>
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">
                    {formatRam(profile?.max_ram_capacity_mb || 16384)} (في {profile?.ram_slots_count || 2} منافذ)
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">منافذ التخزين والتوسعة:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.sata_ports_count || 2}x SATA • {profile?.pcie_slots_summary || 'PCIe 3.0'}
                  </span>
                </div>
              </div>
            </div>

            {/* CPU Architecture Grid */}
            <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden bg-white dark:bg-zinc-900">
              <div className="px-4 py-2.5 bg-zinc-50 dark:bg-zinc-800/60 border-b border-zinc-200 dark:border-zinc-800 text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-zinc-500" />
                <span>المعمارية والمعالج (Processor Architecture)</span>
              </div>
              <div className="grid grid-cols-2 text-xs divide-x divide-y divide-zinc-100 dark:divide-zinc-800">
                <div className="p-3.5 col-span-2">
                  <span className="text-zinc-400 block mb-1">اسم المعالج بالكامل:</span>
                  <span className="font-mono font-medium text-zinc-900 dark:text-zinc-100">
                    {profile?.cpu_model || 'Intel Core i7-4600M @ 2.90GHz'}
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">الأنوية والمسارات:</span>
                  <span className="font-mono text-zinc-900 dark:text-zinc-100">
                    {profile?.cpu_cores || 2} Cores / {profile?.cpu_threads || 4} Threads
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">المقبس والمعمارية:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.cpu_socket || 'Socket 947'} ({profile?.cpu_code_name || 'Haswell'})
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">التردد الأساسي والتيربو:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.cpu_base_clock_mhz || 2900} MHz / {profile?.cpu_boost_clock_mhz || 3600} MHz
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">كاش واستهلاك الطاقة:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    L3: {profile?.cpu_l3_cache_kb ? `${profile.cpu_l3_cache_kb / 1024}MB` : '4MB'} • TDP: {profile?.cpu_tdp_watts || 37}W
                  </span>
                </div>
              </div>
            </div>

            {/* Display & OS Grid */}
            <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden bg-white dark:bg-zinc-900">
              <div className="px-4 py-2.5 bg-zinc-50 dark:bg-zinc-800/60 border-b border-zinc-200 dark:border-zinc-800 text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                <Monitor className="w-4 h-4 text-zinc-500" />
                <span>الشاشة وبيئة التشغيل والشبكة</span>
              </div>
              <div className="grid grid-cols-2 text-xs divide-x divide-y divide-zinc-100 dark:divide-zinc-800">
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">نظام التشغيل:</span>
                  <span className="font-medium text-zinc-900 dark:text-zinc-100">
                    {profile?.os_name || 'Windows 10 Pro 64-bit'}
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">الشاشة والأبعاد:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.screen_size_inch ? `${profile.screen_size_inch}"` : '14.0"'} • {profile?.screen_resolution || '1600x900'}
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">عنوان الماك (MAC):</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.primary_mac_address || '34:E6:D7:12:4F:88'}
                  </span>
                </div>
                <div className="p-3.5">
                  <span className="text-zinc-400 block mb-1">اسم الجهاز على الشبكة:</span>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {profile?.hostname || 'WORK-PC'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 3: AUDIT HISTORY                                     */}
        {/* ======================================================== */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            {(!device.history || device.history.length === 0) ? (
              <div className="p-6 border border-dashed border-zinc-200 dark:border-zinc-800 rounded-lg text-center text-xs text-zinc-400">
                لا توجد سجلات سابقة مسجلة لهذا الجهاز
              </div>
            ) : (
              <div className="relative border-r border-zinc-200 dark:border-zinc-800 mr-2 space-y-5">
                {device.history.map((log) => (
                  <div key={log.id} className="relative pr-6">
                    {/* Timeline dot */}
                    <div className="absolute -right-1.5 top-1 w-3 h-3 rounded-full bg-white dark:bg-zinc-900 border-2 border-zinc-900 dark:border-zinc-100" />
                    <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                      {log.action === 'installed' ? 'تركيب / فحص عتاد' :
                       log.action === 'uninstalled' ? 'فك ونقل قطعة' :
                       log.action === 'assigned' ? 'تسليم كعهدة' :
                       log.action === 'returned' ? 'استرجاع من عهدة' : log.action}
                    </div>
                    <div className="text-xs text-zinc-600 dark:text-zinc-300 mt-1">
                      {log.notes || 'لا توجد ملاحظات إضافية'}
                    </div>
                    <div className="text-[11px] text-zinc-400 mt-1 font-mono">
                      {formatRelativeTime(log.created_at)} ({new Date(log.created_at).toLocaleDateString('ar-EG')})
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </SlideOverDrawer>

      {/* Unmount Modal confirmation */}
      {unmountPartModal && (
        <Modal
          isOpen={true}
          onClose={() => setUnmountPartModal(null)}
          title="فك القطعة ونقلها إلى درج الغيار"
          subtitle={`سيتم فك "${unmountPartModal.name}" وتحديث مواصفات الجهاز تلقائياً`}
          maxWidth="md"
          footer={
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setUnmountPartModal(null)}
              >
                إلغاء
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={isUnmounting}
                onClick={handleConfirmUnmount}
              >
                تأكيد الفك والحفظ بالدرج
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                اختر أو اكتب وسم صندوق التخزين:
              </label>
              <input
                type="text"
                value={storageBoxInput}
                onChange={(e) => setStorageBoxInput(e.target.value)}
                placeholder="مثال: درج 1 - علبة A"
                className="w-full px-3 py-2 text-sm bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
                autoFocus
              />
              <p className="mt-1 text-[11px] text-zinc-500">
                سيتم وسم القطعة بهذا الصندوق لسهولة العثور عليها لاحقاً في درج القطع.
              </p>
            </div>

            <div className="p-3 bg-zinc-50 dark:bg-zinc-800/60 rounded-md border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-600 dark:text-zinc-400 space-y-1">
              <div><strong>القطعة:</strong> {unmountPartModal.name}</div>
              <div><strong>المنفذ الحالي:</strong> {unmountPartModal.slot_or_bus || 'افتراضي'}</div>
              {unmountPartModal.serial_number && <div><strong>السيريال:</strong> <span className="font-mono">{unmountPartModal.serial_number}</span></div>}
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};

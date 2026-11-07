import React, { useState } from 'react';
import { 
  Archive, 
  Wrench, 
  UserCheck, 
  Box, 
  Cpu, 
  HardDrive, 
  Layers, 
  Radio, 
  Search,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Asset, DeviceWithDetails, Person, ComponentTypeSlug } from '../types';
import { Button } from '../components/Button';
import { Modal } from '../components/Modal';
import { formatRam, formatStorage } from '../lib/utils';

interface DrawerPageProps {
  parts: Asset[];
  devices: DeviceWithDetails[];
  persons: Person[];
  searchQuery: string;
  onMountPart: (partId: string, deviceId: string, slotName: string) => Promise<void>;
  onAssignCustody: (assetId: string, personId: string, notes?: string) => Promise<void>;
}

export const DrawerPage: React.FC<DrawerPageProps> = ({
  parts,
  devices,
  persons,
  searchQuery,
  onMountPart,
  onAssignCustody,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  // Mount modal state
  const [mountModalPart, setMountModalPart] = useState<Asset | null>(null);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [slotInput, setSlotInput] = useState<string>('');
  const [isMounting, setIsMounting] = useState(false);

  // Lend / Custody modal state
  const [lendModalPart, setLendModalPart] = useState<Asset | null>(null);
  const [selectedPersonId, setSelectedPersonId] = useState<string>('');
  const [lendNotes, setLendNotes] = useState<string>('');
  const [isLending, setIsLending] = useState(false);

  // Filter tabs
  const categories: { id: string; label: string; icon: string }[] = [
    { id: 'ALL', label: 'الكل', icon: '🗄️' },
    { id: 'RAM', label: 'الرامات', icon: '🧠' },
    { id: 'STORAGE', label: 'التخزين', icon: '💾' },
    { id: 'GPU', label: 'كروت الشاشة', icon: '🎮' },
    { id: 'NETWORK', label: 'الشبكات', icon: '📡' },
    { id: 'OTHER', label: 'أخرى', icon: '🔧' },
  ];

  const filteredParts = parts.filter(p => {
    // category filter
    if (selectedCategory !== 'ALL' && p.component_type_slug !== selectedCategory) {
      return false;
    }
    // search query filter
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      p.name.toLowerCase().includes(q) ||
      (p.serial_number && p.serial_number.toLowerCase().includes(q)) ||
      (p.storage_box_label && p.storage_box_label.toLowerCase().includes(q)) ||
      (p.notes && p.notes.toLowerCase().includes(q))
    );
  });

  const getCategoryCount = (catId: string) => {
    if (catId === 'ALL') return parts.length;
    return parts.filter(p => p.component_type_slug === catId).length;
  };

  const getPartIcon = (slug?: ComponentTypeSlug) => {
    switch (slug) {
      case 'RAM': return '🧠';
      case 'STORAGE': return '💾';
      case 'GPU': return '🎮';
      case 'NETWORK': return '📡';
      default: return '📦';
    }
  };

  // Open mount modal
  const handleOpenMount = (part: Asset) => {
    setMountModalPart(part);
    setSelectedDeviceId(devices[0]?.id || '');
    // Suggest default slot
    if (part.component_type_slug === 'RAM') {
      setSlotInput('ChannelA-DIMM1');
    } else if (part.component_type_slug === 'STORAGE') {
      setSlotInput('SATA Port 1');
    } else {
      setSlotInput('Slot 1');
    }
  };

  const handleConfirmMount = async () => {
    if (!mountModalPart || !selectedDeviceId) return;
    setIsMounting(true);
    try {
      await onMountPart(mountModalPart.id, selectedDeviceId, slotInput || 'منفذ قياسي');
      setMountModalPart(null);
    } finally {
      setIsMounting(false);
    }
  };

  // Open lend modal
  const handleOpenLend = (part: Asset) => {
    setLendModalPart(part);
    setSelectedPersonId(persons[0]?.id || '');
    setLendNotes('');
  };

  const handleConfirmLend = async () => {
    if (!lendModalPart || !selectedPersonId) return;
    setIsLending(true);
    try {
      await onAssignCustody(lendModalPart.id, selectedPersonId, lendNotes);
      setLendModalPart(null);
    } finally {
      setIsLending(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-base font-semibold text-zinc-950 dark:text-zinc-50">
            درج قطع الغيار المفكوكة ({parts.length})
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            متابعة القطع المخزنة في الصناديق والأدراج والجاهزة للتركيب أو الإعارة
          </p>
        </div>

        {/* Medusa Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {categories.map((cat) => {
            const count = getCategoryCount(cat.id);
            const isActive = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  isActive
                    ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-xs'
                    : 'bg-zinc-100 text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/70 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200'
                }`}
              >
                <span>{cat.icon}</span>
                <span>{cat.label}</span>
                <span className={`text-[11px] px-1.5 py-0.2 rounded-full font-mono ${
                  isActive ? 'bg-white/20 text-white dark:bg-black/20 dark:text-zinc-900' : 'text-zinc-400'
                }`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Parts Grid */}
      {filteredParts.length === 0 ? (
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-12 text-center text-zinc-500 text-sm">
          <Archive className="w-10 h-10 mx-auto text-zinc-300 dark:text-zinc-700 mb-3" />
          <p>لا توجد قطع غيار في هذا التصنيف حالياً</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredParts.map((part) => (
            <div
              key={part.id}
              className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 shadow-subtle hover:border-zinc-300 dark:hover:border-zinc-700 transition-all flex flex-col justify-between group"
            >
              {/* Part Header & Specs */}
              <div>
                <div className="flex items-start justify-between gap-3 mb-2.5">
                  <div className="flex items-start gap-2.5">
                    <span className="text-xl p-2 rounded-md bg-zinc-100 dark:bg-zinc-800 leading-none">
                      {getPartIcon(part.component_type_slug)}
                    </span>
                    <div>
                      <h3 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 line-clamp-2">
                        {part.name}
                      </h3>
                      <div className="font-mono text-[11px] text-zinc-400 mt-0.5">
                        {part.serial_number ? `SN: ${part.serial_number}` : 'بدون سيريال مسجل'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Storage location badge */}
                <div className="mb-3">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-zinc-100 dark:bg-zinc-800/80 text-zinc-700 dark:text-zinc-300 border border-zinc-200/60 dark:border-zinc-700/60">
                    <Box className="w-3.5 h-3.5 text-zinc-500" />
                    <span>{part.storage_box_label || 'غير محدد الصندوق'}</span>
                  </span>
                </div>

                {/* Technical specs pill */}
                <div className="text-[11px] text-zinc-600 dark:text-zinc-400 space-y-1 mb-4 font-mono bg-zinc-50 dark:bg-zinc-800/40 p-2.5 rounded border border-zinc-100 dark:border-zinc-800">
                  {part.specs?.capacity_mb && (
                    <div>السعة: {formatRam(part.specs.capacity_mb)} {part.specs.type || ''} {part.specs.speed_mhz ? `@ ${part.specs.speed_mhz}MHz` : ''}</div>
                  )}
                  {part.specs?.capacity_gb && (
                    <div>السعة: {formatStorage(part.specs.capacity_gb)} ({part.specs.interface || 'SATA'} {part.specs.type || ''})</div>
                  )}
                  {part.specs?.vram_mb && (
                    <div>الذاكرة: {formatRam(part.specs.vram_mb)} ({part.specs.interface || 'PCIe'})</div>
                  )}
                  {part.notes && (
                    <div className="font-sans text-[11px] text-zinc-500 pt-1 border-t border-zinc-200/50 dark:border-zinc-700/50">
                      {part.notes}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center gap-2">
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleOpenMount(part)}
                  className="flex-1 text-xs"
                >
                  <Wrench className="w-3.5 h-3.5" />
                  <span>تركيب في جهاز</span>
                </Button>

                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleOpenLend(part)}
                  className="text-xs px-2.5"
                  title="إعارة هذه القطعة لشخص"
                >
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>إعارة</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Mount Modal */}
      {mountModalPart && (
        <Modal
          isOpen={true}
          onClose={() => setMountModalPart(null)}
          title="تركيب القطعة في جهاز"
          subtitle={`حدد الجهاز المراد تركيب "${mountModalPart.name}" بداخله`}
          maxWidth="md"
          footer={
            <>
              <Button variant="secondary" size="sm" onClick={() => setMountModalPart(null)}>
                إلغاء
              </Button>
              <Button variant="primary" size="sm" isLoading={isMounting} onClick={handleConfirmMount}>
                تأكيد التركيب وتحديث الجهاز
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                اختر الجهاز المستهدف:
              </label>
              <select
                value={selectedDeviceId}
                onChange={(e) => setSelectedDeviceId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.profile?.cpu_model?.split('@')[0] || 'جهاز'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                اسم المنفذ (Slot / Port):
              </label>
              <input
                type="text"
                value={slotInput}
                onChange={(e) => setSlotInput(e.target.value)}
                placeholder="مثال: ChannelA-DIMM1 أو SATA Port 1"
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400 font-mono"
              />
              <p className="mt-1 text-[11px] text-zinc-500">
                اسم المنفذ الفيزيائي باللوحة الأم لتتبعه في تقارير الفحص القادمة.
              </p>
            </div>

            <div className="p-3 bg-zinc-50 dark:bg-zinc-800/60 rounded-md border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-600 dark:text-zinc-400">
              <span className="font-semibold block mb-1">القطعة:</span>
              <span>{mountModalPart.name}</span>
              {mountModalPart.serial_number && (
                <div className="font-mono text-[11px] mt-0.5">SN: {mountModalPart.serial_number}</div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Lend / Custody Modal */}
      {lendModalPart && (
        <Modal
          isOpen={true}
          onClose={() => setLendModalPart(null)}
          title="إعارة القطعة لشخص"
          subtitle={`تسليم "${lendModalPart.name}" كعهدة مسجلة`}
          maxWidth="md"
          footer={
            <>
              <Button variant="secondary" size="sm" onClick={() => setLendModalPart(null)}>
                إلغاء
              </Button>
              <Button variant="primary" size="sm" isLoading={isLending} onClick={handleConfirmLend}>
                تسليم العهدة
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                اختر الشخص المستلم:
              </label>
              <select
                value={selectedPersonId}
                onChange={(e) => setSelectedPersonId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
              >
                {persons.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.relationship || 'جهة اتصال'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                ملاحظات أو سبب الإعارة:
              </label>
              <textarea
                value={lendNotes}
                onChange={(e) => setLendNotes(e.target.value)}
                placeholder="مثال: تجربة تشغيل على جهاز مكتبي لمدة أسبوع..."
                rows={3}
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400 font-sans"
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

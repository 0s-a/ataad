import React, { useState } from 'react';
import { 
  Users, 
  Phone, 
  RotateCcw, 
  Clock, 
  Laptop, 
  CheckCircle, 
  AlertCircle,
  Plus,
  Box,
  UserCheck
} from 'lucide-react';
import { Person, Asset, CustodyLog } from '../types';
import { Button } from '../components/Button';
import { Modal } from '../components/Modal';
import { formatRelativeTime } from '../lib/utils';

interface CustodyPageProps {
  persons: Person[];
  searchQuery: string;
  onReturnCustody: (assetId: string, storageBox: string, notes?: string) => Promise<void>;
}

export const CustodyPage: React.FC<CustodyPageProps> = ({
  persons,
  searchQuery,
  onReturnCustody,
}) => {
  const [selectedPersonId, setSelectedPersonId] = useState<string>(persons[0]?.id || '');
  
  // Return modal state
  const [returnItemModal, setReturnItemModal] = useState<Asset | null>(null);
  const [storageBoxInput, setStorageBoxInput] = useState('درج 1 - علبة A');
  const [returnNotes, setReturnNotes] = useState('');
  const [isReturning, setIsReturning] = useState(false);

  const filteredPersons = persons.filter(p => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      p.name.toLowerCase().includes(q) ||
      (p.phone && p.phone.includes(q)) ||
      (p.relationship && p.relationship.toLowerCase().includes(q))
    );
  });

  const selectedPerson = persons.find(p => p.id === selectedPersonId) || filteredPersons[0];

  const handleOpenReturn = (asset: Asset) => {
    setReturnItemModal(asset);
    setStorageBoxInput('درج 1 - علبة A');
    setReturnNotes('تم الاسترجاع بحالة سليمة');
  };

  const handleConfirmReturn = async () => {
    if (!returnItemModal) return;
    setIsReturning(true);
    try {
      await onReturnCustody(returnItemModal.id, storageBoxInput, returnNotes);
      setReturnItemModal(null);
    } finally {
      setIsReturning(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-base font-semibold text-zinc-950 dark:text-zinc-50">
          مركز العُهد والأشخاص ({persons.length})
        </h1>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          تتبع الأجهزة والقطع المعارة للأصدقاء والزملاء وسجل استردادها
        </p>
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Right Column: Contact List (4 cols) */}
        <div className="lg:col-span-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-subtle overflow-hidden">
          <div className="p-3.5 border-b border-zinc-200/80 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/60 flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
              جهات الاتصال
            </span>
            <span className="text-[11px] text-zinc-400 font-mono">
              {filteredPersons.length} أشخاص
            </span>
          </div>

          <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {filteredPersons.map((person) => {
              const isSelected = selectedPerson?.id === person.id;
              const custodyCount = person.current_assets?.length || person.active_custody_count || 0;

              return (
                <div
                  key={person.id}
                  onClick={() => setSelectedPersonId(person.id)}
                  className={`p-3.5 cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-zinc-100/90 dark:bg-zinc-800/80 border-r-2 border-zinc-900 dark:border-zinc-100'
                      : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium text-xs text-zinc-950 dark:text-zinc-50">
                      {person.name}
                    </div>
                    {custodyCount > 0 ? (
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900 font-mono">
                        {custodyCount} عهدة
                      </span>
                    ) : (
                      <span className="text-[11px] text-zinc-400 font-mono">
                        لا عهدة
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mt-1 text-[11px] text-zinc-500">
                    <span>{person.relationship || 'صديق'}</span>
                    {person.phone && (
                      <>
                        <span>•</span>
                        <span className="font-mono">{person.phone}</span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Left Column: Selected Person Details & Custody Records (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {selectedPerson ? (
            <>
              {/* Person Summary Card */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 shadow-subtle flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-zinc-950 dark:text-zinc-50">
                    {selectedPerson.name}
                  </h2>
                  <div className="flex items-center gap-3 text-xs text-zinc-500 mt-1">
                    <span>الصفة: {selectedPerson.relationship || 'جهة اتصال'}</span>
                    {selectedPerson.phone && (
                      <>
                        <span>•</span>
                        <span className="font-mono flex items-center gap-1">
                          <Phone className="w-3 h-3 text-zinc-400" />
                          {selectedPerson.phone}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="text-left font-mono text-xs">
                  <span className="text-zinc-400 block text-[11px]">العهدة الحالية:</span>
                  <span className="text-base font-bold text-zinc-900 dark:text-zinc-100">
                    {selectedPerson.current_assets?.length || 0} أصول
                  </span>
                </div>
              </div>

              {/* Active Custody Table */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-subtle overflow-hidden">
                <div className="p-3.5 border-b border-zinc-200/80 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/60 flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <UserCheck className="w-4 h-4 text-amber-500" />
                    <span>العهدة النشطة حالياً بحوزته</span>
                  </span>
                  <span className="text-[11px] text-zinc-400 font-mono">
                    {selectedPerson.current_assets?.length || 0} أصول
                  </span>
                </div>

                {(!selectedPerson.current_assets || selectedPerson.current_assets.length === 0) ? (
                  <div className="p-8 text-center text-xs text-zinc-400">
                    لا توجد أي عهدة نشطة حالياً بحوزة هذا الشخص
                  </div>
                ) : (
                  <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
                    {selectedPerson.current_assets.map((asset) => (
                      <div key={asset.id} className="p-4 flex items-center justify-between gap-4">
                        <div className="space-y-1">
                          <div className="font-medium text-xs text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                            <span>{asset.name}</span>
                          </div>
                          <div className="flex items-center gap-3 text-[11px] text-zinc-500 font-mono">
                            {asset.serial_number && <span>SN: {asset.serial_number}</span>}
                            <span>•</span>
                            <span>تاريخ التسليم: {formatRelativeTime(asset.assigned_at || asset.created_at)}</span>
                          </div>
                        </div>

                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleOpenReturn(asset)}
                          className="text-xs text-zinc-700 dark:text-zinc-300"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-zinc-400" />
                          <span>استرجاع للدرج</span>
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Past History Table */}
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-subtle overflow-hidden">
                <div className="p-3.5 border-b border-zinc-200/80 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/60 flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-zinc-400" />
                    <span>السجل التاريخي السابق (ما تم استرداده)</span>
                  </span>
                </div>

                {(!selectedPerson.past_logs || selectedPerson.past_logs.length === 0) ? (
                  <div className="p-6 text-center text-xs text-zinc-400">
                    لا توجد سجلات استرجاع تاريخية سابقة
                  </div>
                ) : (
                  <div className="divide-y divide-zinc-100 dark:divide-zinc-800 text-xs">
                    {selectedPerson.past_logs.map((log) => (
                      <div key={log.id} className="p-3.5 flex items-center justify-between">
                        <div>
                          <div className="font-medium text-zinc-800 dark:text-zinc-200">
                            {log.asset_name || 'قطعة مسترجعة'}
                          </div>
                          <div className="text-[11px] text-zinc-400 mt-0.5">
                            {log.notes || 'تم الاسترجاع بحالة سليمة'}
                          </div>
                        </div>
                        <div className="text-[11px] text-zinc-400 font-mono">
                          {formatRelativeTime(log.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-zinc-400 text-xs">
              الرجاء اختيار جهة اتصال لعرض تفاصيل العهدة
            </div>
          )}
        </div>
      </div>

      {/* Return to Drawer Modal */}
      {returnItemModal && (
        <Modal
          isOpen={true}
          onClose={() => setReturnItemModal(null)}
          title="استرجاع العهدة وحفظها في الدرج"
          subtitle={`سيتم إنهاء عهدة "${returnItemModal.name}" وتسجيل حركة الاسترجاع`}
          maxWidth="md"
          footer={
            <>
              <Button variant="secondary" size="sm" onClick={() => setReturnItemModal(null)}>
                إلغاء
              </Button>
              <Button variant="primary" size="sm" isLoading={isReturning} onClick={handleConfirmReturn}>
                تأكيد الاسترجاع وحفظ بالدرج
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                حدد صندوق التخزين في درج الغيار:
              </label>
              <input
                type="text"
                value={storageBoxInput}
                onChange={(e) => setStorageBoxInput(e.target.value)}
                placeholder="مثال: درج 1 - علبة A"
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                ملاحظات الفحص والاستلام:
              </label>
              <input
                type="text"
                value={returnNotes}
                onChange={(e) => setReturnNotes(e.target.value)}
                placeholder="مثال: تم فحص السلامة والقرص سليم..."
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

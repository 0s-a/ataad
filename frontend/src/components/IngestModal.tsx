import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Cpu, 
  CircuitBoard, 
  HardDrive, 
  Layers, 
  Check, 
  RefreshCw 
} from 'lucide-react';
import { Modal } from './Modal';
import { Button } from './Button';
import { CPUZParsePreview } from '../types';
import { apiClient } from '../api/client';
import { formatRam, formatStorage } from '../lib/utils';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isParsing, setIsParsing] = useState(false);
  const [preview, setPreview] = useState<CPUZParsePreview | null>(null);
  const [customDeviceName, setCustomDeviceName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileProcess = async (fileToProcess: File) => {
    setFile(fileToProcess);
    setIsParsing(true);
    try {
      // Handle both UTF-8 and UTF-16 text
      const arrayBuffer = await fileToProcess.arrayBuffer();
      let text = '';
      try {
        // Try UTF-16LE first if starts with BOM or null bytes
        const uint8 = new Uint8Array(arrayBuffer);
        if (uint8.length > 2 && uint8[1] === 0) {
          text = new TextDecoder('utf-16le').decode(arrayBuffer);
        } else {
          text = new TextDecoder('utf-8').decode(arrayBuffer);
        }
      } catch {
        text = await fileToProcess.text();
      }

      setFileContent(text);
      const parsedPreview = await apiClient.previewCpuZ(text);
      setPreview(parsedPreview);
      setCustomDeviceName(parsedPreview.device_name || 'جهاز مستورد جديد');
    } catch (err) {
      console.error('Error parsing CPU-Z report:', err);
    } finally {
      setIsParsing(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleCommit = async () => {
    if (!preview) return;
    setIsSubmitting(true);
    try {
      const res = await apiClient.ingestCpuZ(preview, customDeviceName);
      if (res.success) {
        onSuccess(res.message);
        handleReset();
        onClose();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setFileContent('');
    setPreview(null);
    setCustomDeviceName('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const loadDemoReport = async () => {
    setIsParsing(true);
    try {
      const sampleText = `CPU-Z TXT Report
Specification   Intel(R) Core(TM) i7-4600M CPU @ 2.90GHz
Mainboard Model 0K9GNV
Mainboard Vendor Dell Inc.
Windows Version Microsoft Windows 10 Pro 64-bit
Memory Type     DDR3
Memory Size     8 GBytes
Memory SPD
Slot #0
Module Size     4096 MBytes
Max Bandwidth   DDR3-1600 (800 MHz)
Manufacturer    Samsung
Part Number     M471B5173QH0-YK0
Slot #1
Module Size     4096 MBytes
Max Bandwidth   DDR3-1600 (800 MHz)
Manufacturer    Kingston
Part Number     KVR16LS11/4
`;
      setFileContent(sampleText);
      const parsedPreview = await apiClient.previewCpuZ(sampleText);
      setPreview(parsedPreview);
      setCustomDeviceName(parsedPreview.device_name || 'Dell Latitude E6440');
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="استيراد ومعاينة تقرير CPU-Z"
      subtitle="سحب وإفلات ملف التقرير النصي (.txt) لقراءة مواصفات العتاد وربطها بنقرة واحدة"
      maxWidth="2xl"
      footer={
        preview ? (
          <>
            <Button variant="secondary" size="sm" onClick={handleReset}>
              تغيير الملف
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
              onClick={handleCommit}
            >
              <Check className="w-4 h-4" />
              <span>تأكيد الحفظ في عَتاد</span>
            </Button>
          </>
        ) : (
          <Button variant="secondary" size="sm" onClick={onClose}>
            إلغاء
          </Button>
        )
      }
    >
      {!preview ? (
        <div className="space-y-4">
          {/* Dropzone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? 'border-zinc-900 bg-zinc-100/80 dark:border-zinc-100 dark:bg-zinc-800'
                : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 bg-zinc-50/50 dark:bg-zinc-800/20'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileProcess(e.target.files[0]);
                }
              }}
            />

            <div className="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mx-auto mb-3 text-zinc-600 dark:text-zinc-300">
              <Upload className="w-5 h-5" />
            </div>

            <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              اسحب تقرير CPU-Z هنا أو اضغط للاختيار
            </h4>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              يدعم ملفات تقرير CPU-Z النصية بتنسيق TXT
            </p>
          </div>

          {/* Quick Demo Option */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-100/60 dark:bg-zinc-800/40 border border-zinc-200/60 dark:border-zinc-700/60 text-xs">
            <span className="text-zinc-600 dark:text-zinc-400">
              تريد تجربة استيراد سريع ببيانات عينة واقعية؟
            </span>
            <button
              type="button"
              onClick={loadDemoReport}
              disabled={isParsing}
              className="font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
            >
              تحميل نموذج تقرير CPU-Z تجريبي
            </button>
          </div>
        </div>
      ) : (
        /* Pre-flight Preview Grid */
        <div className="space-y-5 animate-fadeIn">
          {/* Match Status Banner */}
          <div className={`p-3.5 rounded-lg border flex items-center justify-between text-xs ${
            preview.is_known_device 
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900'
              : 'bg-sky-50 text-sky-800 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-900'
          }`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span className="font-medium">
                {preview.is_known_device
                  ? 'جهاز مطابق مسجل مسبقاً — سيتم تحديث سجلات الفحص والعتاد'
                  : 'جهاز جديد كلياً — سيتم إنشاؤه وتسجيل كافة مكوناته'}
              </span>
            </div>
            {preview.system_serial && (
              <span className="font-mono text-[11px] bg-white/60 dark:bg-black/30 px-2 py-0.5 rounded">
                SN: {preview.system_serial}
              </span>
            )}
          </div>

          {/* Device Friendly Name Input */}
          <div>
            <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              الاسم الودي للجهاز في عَتاد:
            </label>
            <input
              type="text"
              value={customDeviceName}
              onChange={(e) => setCustomDeviceName(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400 font-medium"
            />
          </div>

          {/* Core Specs Preview Grid */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            {/* CPU */}
            <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/40">
              <span className="text-zinc-400 block text-[11px] mb-1">المعالج المكتشف:</span>
              <span className="font-mono font-medium text-zinc-900 dark:text-zinc-100 block truncate" title={preview.cpu_model}>
                {preview.cpu_model || 'Intel Core i7-4600M'}
              </span>
              <span className="text-[11px] text-zinc-500 font-mono mt-0.5 block">
                {preview.cpu_cores || 2} Cores / {preview.cpu_threads || 4} Threads
              </span>
            </div>

            {/* Motherboard */}
            <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/40">
              <span className="text-zinc-400 block text-[11px] mb-1">اللوحة الأم المكتشفة:</span>
              <span className="font-mono font-medium text-zinc-900 dark:text-zinc-100 block">
                {preview.motherboard_vendor || 'Dell'} {preview.motherboard_model || '0K9GNV'}
              </span>
              <span className="text-[11px] text-zinc-500 font-mono mt-0.5 block">
                Chipset: {preview.chipset || 'Intel Haswell'}
              </span>
            </div>
          </div>

          {/* Detected Components Tree */}
          <div className="space-y-3">
            <h5 className="text-xs font-semibold text-zinc-900 dark:text-zinc-100">
              القطع المرصودة الجاهزة للتسجيل:
            </h5>

            <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg divide-y divide-zinc-100 dark:divide-zinc-800 text-xs overflow-hidden">
              {/* RAMs */}
              {preview.detected_rams.map((ram, i) => (
                <div key={i} className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>🧠</span>
                    <div>
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">
                        {ram.manufacturer ? `${ram.manufacturer} ` : ''}{ram.model}
                      </span>
                      <span className="text-zinc-400 mr-2 text-[11px] font-mono">({ram.slot})</span>
                    </div>
                  </div>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {formatRam(ram.capacity_mb)} {ram.type || 'DDR3'}
                  </span>
                </div>
              ))}

              {/* Disks */}
              {preview.detected_disks.map((disk, i) => (
                <div key={i} className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>💾</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {disk.model}
                    </span>
                  </div>
                  <span className="font-mono text-zinc-700 dark:text-zinc-300">
                    {formatStorage(disk.capacity_gb)} {disk.type}
                  </span>
                </div>
              ))}

              {/* GPUs */}
              {preview.detected_gpus.map((gpu, i) => (
                <div key={i} className="p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>🎮</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100">
                      {gpu.name}
                    </span>
                  </div>
                  <span className="text-zinc-500 text-[11px]">
                    {gpu.is_integrated ? 'مدمج' : 'منفصل'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
};

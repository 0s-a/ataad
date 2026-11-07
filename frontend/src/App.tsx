import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { Header } from './components/Header';
import { StatsBar } from './components/StatsBar';
import { DevicesPage } from './pages/DevicesPage';
import { DrawerPage } from './pages/DrawerPage';
import { CustodyPage } from './pages/CustodyPage';
import { CatalogPage } from './pages/CatalogPage';
import { IngestModal } from './components/IngestModal';
import { Modal } from './components/Modal';
import { Button } from './components/Button';
import { DeviceWithDetails, Asset, Person, StatsSummary, AssetModel } from './types';
import { apiClient } from './api/client';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export function App() {
  // Navigation & View
  const [currentTab, setCurrentTab] = useState<NavTab>('devices');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dark mode
  const [isDark, setIsDark] = useState(() => {
    return localStorage.getItem('ataad_theme') === 'dark' ||
      (!('ataad_theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });

  // Data states
  const [devices, setDevices] = useState<DeviceWithDetails[]>([]);
  const [drawerParts, setDrawerParts] = useState<Asset[]>([]);
  const [persons, setPersons] = useState<Person[]>([]);
  const [catalogModels, setCatalogModels] = useState<AssetModel[]>([]);
  const [stats, setStats] = useState<StatsSummary>({
    active_devices_count: 0,
    total_ram_gb: 0,
    total_storage_tb: 0,
    drawer_parts_count: 0,
  });

  // Selected device for drawer
  const [selectedDevice, setSelectedDevice] = useState<DeviceWithDetails | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Ingest modal
  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);

  // New device manual modal
  const [isNewDeviceModalOpen, setIsNewDeviceModalOpen] = useState(false);
  const [newDeviceName, setNewDeviceName] = useState('');
  const [newDeviceChassis, setNewDeviceChassis] = useState('laptop');
  const [newDeviceCpu, setNewDeviceCpu] = useState('');

  // Toast notification
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((prev) => (prev === msg ? null : prev));
    }, 4000);
  };

  // Sync theme
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('ataad_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('ataad_theme', 'light');
    }
  }, [isDark]);

  // Load all initial data
  const loadData = useCallback(async () => {
    const [devs, parts, pers, cats, st] = await Promise.all([
      apiClient.getDevices(),
      apiClient.getDrawerParts(),
      apiClient.getPersons(),
      apiClient.getCatalogModels(),
      apiClient.getStats(),
    ]);
    setDevices(devs);
    setDrawerParts(parts);
    setPersons(pers);
    setCatalogModels(cats);
    setStats(st);

    // Keep selected device updated if open
    if (selectedDevice) {
      const refreshed = devs.find((d) => d.id === selectedDevice.id);
      if (refreshed) setSelectedDevice(refreshed);
    }
  }, [selectedDevice]);

  useEffect(() => {
    loadData();
  }, []);

  // Handlers
  const handleSelectDevice = (device: DeviceWithDetails) => {
    setSelectedDevice(device);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
  };

  const handleUnmountPart = async (partId: string, storageBox: string) => {
    const res = await apiClient.unmountComponent(partId, storageBox);
    if (res.success) {
      showToast(res.message);
      await loadData();
    }
  };

  const handleMountPart = async (partId: string, deviceId: string, slotName: string) => {
    const res = await apiClient.mountComponent(partId, deviceId, slotName);
    if (res.success) {
      showToast(res.message);
      await loadData();
    }
  };

  const handleAssignCustody = async (assetId: string, personId: string, notes?: string) => {
    const res = await apiClient.assignCustody(assetId, personId, notes);
    if (res.success) {
      showToast(res.message);
      await loadData();
    }
  };

  const handleReturnCustody = async (assetId: string, storageBox: string, notes?: string) => {
    const res = await apiClient.returnCustody(assetId, storageBox, notes);
    if (res.success) {
      showToast(res.message);
      await loadData();
    }
  };

  const handleCreateManualDevice = async () => {
    if (!newDeviceName.trim()) return;
    const devId = `dev-${Date.now()}`;
    const newDev: DeviceWithDetails = {
      id: devId,
      name: newDeviceName.trim(),
      status: 'active',
      specs: {
        chassis: newDeviceChassis,
        cpu: newDeviceCpu || 'Intel Core i5',
        ram_mb: 8192,
        storage_gb: 256,
      },
      profile: {
        asset_id: devId,
        chassis_subtype: newDeviceChassis,
        cpu_model: newDeviceCpu || 'Intel Core i5',
        total_ram_mb: 8192,
        total_storage_gb: 256,
        ram_slots_count: 2,
        last_scanned_at: new Date().toISOString(),
      },
      components: [],
      history: [
        {
          id: `log-${Date.now()}`,
          asset_id: devId,
          action: 'installed',
          notes: 'إنشاء جهاز جديد يدوياً',
          created_at: new Date().toISOString(),
        },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setDevices((prev) => [newDev, ...prev]);
    setIsNewDeviceModalOpen(false);
    setNewDeviceName('');
    setNewDeviceCpu('');
    showToast(`تم إنشاء الجهاز "${newDev.name}" بنجاح!`);
    await loadData();
  };

  // Compute breadcrumbs
  const getBreadcrumbs = () => {
    switch (currentTab) {
      case 'devices':
        return selectedDevice && isDrawerOpen
          ? ['الأجهزة', selectedDevice.name]
          : ['الأجهزة'];
      case 'drawer':
        return ['درج قطع الغيار'];
      case 'custody':
        return ['مركز العُهد'];
      case 'catalog':
        return ['كتالوج الموديلات'];
      default:
        return ['الرئيسية'];
    }
  };

  // Header primary action config
  const getHeaderAction = () => {
    if (currentTab === 'devices') {
      return {
        label: 'جهاز جديد',
        onClick: () => setIsNewDeviceModalOpen(true),
      };
    }
    return undefined;
  };

  return (
    <div className="h-screen flex overflow-hidden bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 font-sans">
      {/* 1. Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header
          breadcrumbs={getBreadcrumbs()}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          primaryActionLabel={getHeaderAction()?.label}
          onPrimaryAction={getHeaderAction()?.onClick}
        />

        {/* Scrollable Work Area */}
        <main className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Global Quick Stats */}
          <StatsBar stats={stats} />

          {/* Tab Pages */}
          {currentTab === 'devices' && (
            <DevicesPage
              devices={devices}
              searchQuery={searchQuery}
              onSelectDevice={handleSelectDevice}
              selectedDevice={selectedDevice}
              isDrawerOpen={isDrawerOpen}
              onCloseDrawer={handleCloseDrawer}
              onUnmountPart={handleUnmountPart}
              onOpenNewDeviceModal={() => setIsNewDeviceModalOpen(true)}
            />
          )}

          {currentTab === 'drawer' && (
            <DrawerPage
              parts={drawerParts}
              devices={devices}
              persons={persons}
              searchQuery={searchQuery}
              onMountPart={handleMountPart}
              onAssignCustody={handleAssignCustody}
            />
          )}

          {currentTab === 'custody' && (
            <CustodyPage
              persons={persons}
              searchQuery={searchQuery}
              onReturnCustody={handleReturnCustody}
            />
          )}

          {currentTab === 'catalog' && (
            <CatalogPage
              catalogModels={catalogModels}
              searchQuery={searchQuery}
            />
          )}
        </main>
      </div>

      {/* 2. RTL Sidebar on the right */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          setSearchQuery('');
        }}
        onOpenIngest={() => setIsIngestModalOpen(true)}
        counts={{
          devices: devices.length,
          drawer: drawerParts.length,
          custody: persons.reduce((acc, p) => acc + (p.current_assets?.length || p.active_custody_count || 0), 0),
        }}
        isDark={isDark}
        onToggleTheme={() => setIsDark(!isDark)}
      />

      {/* Ingest CPU-Z Modal */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onSuccess={async (msg) => {
          showToast(msg);
          await loadData();
        }}
      />

      {/* New Device Manual Modal */}
      {isNewDeviceModalOpen && (
        <Modal
          isOpen={true}
          onClose={() => setIsNewDeviceModalOpen(false)}
          title="إضافة جهاز حاسوبي جديد"
          subtitle="إنشاء بطاقة جهاز جديد يدوياً في عَتاد"
          maxWidth="md"
          footer={
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsNewDeviceModalOpen(false)}
              >
                إلغاء
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCreateManualDevice}
              >
                حفظ الجهاز
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                اسم الجهاز الودي:
              </label>
              <input
                type="text"
                value={newDeviceName}
                onChange={(e) => setNewDeviceName(e.target.value)}
                placeholder="مثال: لابتوب Dell Latitude E6440"
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                نوع الهيكل (Chassis):
              </label>
              <select
                value={newDeviceChassis}
                onChange={(e) => setNewDeviceChassis(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400"
              >
                <option value="laptop">لابتوب محمول (Laptop)</option>
                <option value="desktop_tower">مكتبي برج (Desktop Tower)</option>
                <option value="sff">مكتبي مدمج (SFF / Mini PC)</option>
                <option value="server_rack">خادم / سيرفر (Server Rack)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                المعالج (اختياري):
              </label>
              <input
                type="text"
                value={newDeviceCpu}
                onChange={(e) => setNewDeviceCpu(e.target.value)}
                placeholder="مثال: Intel Core i7-4600M @ 2.90GHz"
                className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:ring-1 focus:ring-zinc-400 font-mono"
              />
            </div>
          </div>
        </Modal>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 left-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-zinc-900 text-zinc-50 dark:bg-zinc-100 dark:text-zinc-900 rounded-lg shadow-xl text-xs font-medium animate-fadeIn border border-zinc-800 dark:border-zinc-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 dark:text-emerald-600 flex-shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}

export default App;

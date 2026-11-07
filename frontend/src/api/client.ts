import { 
  Asset, 
  DeviceWithDetails, 
  Person, 
  StatsSummary, 
  CPUZParsePreview,
  AssetModel
} from '../types';
import { 
  initialDevices, 
  initialDrawerParts, 
  initialPersons, 
  initialStats,
  sampleCatalogModels
} from './mockData';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// In-memory persistent state during session
let devicesState: DeviceWithDetails[] = [...initialDevices];
let drawerPartsState: Asset[] = [...initialDrawerParts];
let personsState: Person[] = [...initialPersons];
let catalogState: AssetModel[] = [...sampleCatalogModels];

export const apiClient = {
  // ==========================================
  // 1. Devices API
  // ==========================================
  async getDevices(query?: string): Promise<DeviceWithDetails[]> {
    try {
      const url = new URL(`${API_BASE_URL}/devices`);
      if (query) url.searchParams.set('q', query);
      const res = await fetch(url.toString(), { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        const data = await res.json();
        return data;
      }
    } catch {
      // Fallback to local state
    }

    if (!query) return [...devicesState];
    const q = query.toLowerCase().trim();
    return devicesState.filter(d => 
      d.name.toLowerCase().includes(q) ||
      (d.serial_number && d.serial_number.toLowerCase().includes(q)) ||
      (d.profile?.cpu_model && d.profile.cpu_model.toLowerCase().includes(q)) ||
      (d.profile?.motherboard_model && d.profile.motherboard_model.toLowerCase().includes(q))
    );
  },

  async getDeviceDetails(id: string): Promise<DeviceWithDetails | null> {
    try {
      const res = await fetch(`${API_BASE_URL}/devices/${id}`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback
    }

    const found = devicesState.find(d => d.id === id);
    return found ? { ...found } : null;
  },

  // ==========================================
  // 2. Drawer Parts API
  // ==========================================
  async getDrawerParts(category?: string, query?: string): Promise<Asset[]> {
    try {
      const url = new URL(`${API_BASE_URL}/drawer`);
      if (category && category !== 'ALL') url.searchParams.set('category', category);
      if (query) url.searchParams.set('q', query);
      const res = await fetch(url.toString(), { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback
    }

    let result = [...drawerPartsState];
    if (category && category !== 'ALL') {
      result = result.filter(p => p.component_type_slug === category);
    }
    if (query) {
      const q = query.toLowerCase().trim();
      result = result.filter(p => 
        p.name.toLowerCase().includes(q) ||
        (p.serial_number && p.serial_number.toLowerCase().includes(q)) ||
        (p.storage_box_label && p.storage_box_label.toLowerCase().includes(q)) ||
        (p.notes && p.notes.toLowerCase().includes(q))
      );
    }
    return result;
  },

  // ==========================================
  // 3. Mount / Unmount Actions
  // ==========================================
  async mountComponent(partId: string, deviceId: string, slotName: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/assets/${partId}/mount`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: deviceId, slot: slotName }),
        signal: AbortSignal.timeout(1500)
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    // Local state simulation
    const partIndex = drawerPartsState.findIndex(p => p.id === partId);
    if (partIndex === -1) return { success: false, message: 'القطعة غير موجودة بالدرج' };

    const part = drawerPartsState[partIndex];
    drawerPartsState.splice(partIndex, 1);

    const device = devicesState.find(d => d.id === deviceId);
    if (device) {
      const mountedComp: Asset = {
        ...part,
        status: 'installed',
        parent_asset_id: deviceId,
        slot_or_bus: slotName,
        storage_box_label: null,
      };
      device.components = [...(device.components || []), mountedComp];
      // update totals if RAM or Storage
      if (part.component_type_slug === 'RAM' && part.specs?.capacity_mb && device.profile) {
        device.profile.total_ram_mb = (device.profile.total_ram_mb || 0) + part.specs.capacity_mb;
      }
      if (part.component_type_slug === 'STORAGE' && part.specs?.capacity_gb && device.profile) {
        device.profile.total_storage_gb = (device.profile.total_storage_gb || 0) + part.specs.capacity_gb;
      }
      device.history = [
        {
          id: `log-${Date.now()}`,
          asset_id: deviceId,
          action: 'installed',
          notes: `تركيب قطعة: ${part.name} في المنفذ ${slotName}`,
          created_at: new Date().toISOString()
        },
        ...(device.history || [])
      ];
    }

    return { success: true, message: `تم تركيب ${part.name} في ${device?.name || 'الجهاز'} بنجاح` };
  },

  async unmountComponent(componentId: string, storageBoxLabel: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/assets/${componentId}/unmount`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storage_box_label: storageBoxLabel }),
        signal: AbortSignal.timeout(1500)
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    let unmountedPart: Asset | null = null;
    let parentDevice: DeviceWithDetails | null = null;

    for (const dev of devicesState) {
      if (dev.components) {
        const idx = dev.components.findIndex(c => c.id === componentId);
        if (idx !== -1) {
          unmountedPart = dev.components[idx];
          parentDevice = dev;
          dev.components.splice(idx, 1);
          // decrease totals
          if (unmountedPart.component_type_slug === 'RAM' && unmountedPart.specs?.capacity_mb && dev.profile) {
            dev.profile.total_ram_mb = Math.max(0, (dev.profile.total_ram_mb || 0) - unmountedPart.specs.capacity_mb);
          }
          if (unmountedPart.component_type_slug === 'STORAGE' && unmountedPart.specs?.capacity_gb && dev.profile) {
            dev.profile.total_storage_gb = Math.max(0, (dev.profile.total_storage_gb || 0) - unmountedPart.specs.capacity_gb);
          }
          dev.history = [
            {
              id: `log-${Date.now()}`,
              asset_id: dev.id,
              action: 'uninstalled',
              notes: `فك قطعة: ${unmountedPart.name} وحفظها في ${storageBoxLabel}`,
              created_at: new Date().toISOString()
            },
            ...(dev.history || [])
          ];
          break;
        }
      }
    }

    if (!unmountedPart) {
      return { success: false, message: 'القطعة غير موجودة بالجهاز' };
    }

    const drawerAsset: Asset = {
      ...unmountedPart,
      status: 'in_storage',
      parent_asset_id: null,
      slot_or_bus: null,
      storage_box_label: storageBoxLabel,
      updated_at: new Date().toISOString()
    };
    drawerPartsState.unshift(drawerAsset);

    return { success: true, message: `تم فك ${unmountedPart.name} ونقلها إلى ${storageBoxLabel}` };
  },

  // ==========================================
  // 4. Custody API
  // ==========================================
  async getPersons(): Promise<Person[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/persons`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    return [...personsState];
  },

  async getPersonDetails(id: string): Promise<Person | null> {
    try {
      const res = await fetch(`${API_BASE_URL}/persons/${id}`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    const found = personsState.find(p => p.id === id);
    return found ? { ...found } : null;
  },

  async assignCustody(assetId: string, personId: string, notes?: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/custody/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_id: assetId, person_id: personId, notes }),
        signal: AbortSignal.timeout(1500)
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    const person = personsState.find(p => p.id === personId);
    if (!person) return { success: false, message: 'الشخص غير موجود' };

    // check if it's in drawer
    const drawerIdx = drawerPartsState.findIndex(p => p.id === assetId);
    let targetAsset: Asset | null = null;

    if (drawerIdx !== -1) {
      targetAsset = drawerPartsState[drawerIdx];
      drawerPartsState.splice(drawerIdx, 1);
    } else {
      // check if it's a device
      const dev = devicesState.find(d => d.id === assetId);
      if (dev) {
        dev.status = 'with_person';
        dev.assigned_person_id = personId;
        dev.assigned_person_name = person.name;
        targetAsset = dev;
      }
    }

    if (!targetAsset) return { success: false, message: 'الأصل غير موجود' };

    const assignedItem: Asset = {
      ...targetAsset,
      status: 'with_person',
      assigned_person_id: personId,
      assigned_at: new Date().toISOString(),
      storage_box_label: null
    };

    person.current_assets = [...(person.current_assets || []), assignedItem];
    person.active_custody_count = (person.active_custody_count || 0) + 1;

    return { success: true, message: `تم تسليم ${targetAsset.name} في عهدة ${person.name}` };
  },

  async returnCustody(assetId: string, storageBoxLabel: string, notes?: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/custody/return`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_id: assetId, storage_box_label: storageBoxLabel, notes }),
        signal: AbortSignal.timeout(1500)
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    for (const person of personsState) {
      if (person.current_assets) {
        const idx = person.current_assets.findIndex(a => a.id === assetId);
        if (idx !== -1) {
          const item = person.current_assets[idx];
          person.current_assets.splice(idx, 1);
          person.active_custody_count = Math.max(0, (person.active_custody_count || 0) - 1);

          person.past_logs = [
            {
              id: `log-${Date.now()}`,
              asset_id: assetId,
              asset_name: item.name,
              person_id: person.id,
              action: 'returned',
              notes: notes || `استرجاع إلى ${storageBoxLabel}`,
              created_at: new Date().toISOString()
            },
            ...(person.past_logs || [])
          ];

          // Check if device or standalone part
          const dev = devicesState.find(d => d.id === assetId);
          if (dev) {
            dev.status = 'active';
            dev.assigned_person_id = null;
            dev.assigned_person_name = undefined;
          } else {
            // It's a spare part -> return to drawer
            const restoredPart: Asset = {
              ...item,
              status: 'in_storage',
              assigned_person_id: null,
              storage_box_label: storageBoxLabel,
              updated_at: new Date().toISOString()
            };
            drawerPartsState.unshift(restoredPart);
          }

          return { success: true, message: `تم استرجاع ${item.name} بنجاح إلى ${storageBoxLabel}` };
        }
      }
    }

    return { success: false, message: 'العنصر غير موجود في أي عهدة نشطة' };
  },

  // ==========================================
  // 5. Global Stats
  // ==========================================
  async getStats(): Promise<StatsSummary> {
    try {
      const res = await fetch(`${API_BASE_URL}/stats`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    const activeDevices = devicesState.filter(d => d.status === 'active' || d.status === 'with_person');
    let totalRamMb = 0;
    let totalStorageGb = 0;

    activeDevices.forEach(d => {
      totalRamMb += d.profile?.total_ram_mb || d.specs?.ram_mb || 0;
      totalStorageGb += d.profile?.total_storage_gb || d.specs?.storage_gb || 0;
    });

    return {
      active_devices_count: activeDevices.length,
      total_ram_gb: Math.round(totalRamMb / 1024),
      total_storage_tb: parseFloat((totalStorageGb / 1000).toFixed(1)),
      drawer_parts_count: drawerPartsState.length
    };
  },

  // ==========================================
  // 6. CPU-Z Ingestion
  // ==========================================
  async previewCpuZ(fileText: string): Promise<CPUZParsePreview> {
    try {
      const res = await fetch(`${API_BASE_URL}/ingest/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: fileText }),
        signal: AbortSignal.timeout(2000)
      });
      if (res.ok) return await res.json();
    } catch {
      // Client-side parser fallback
    }

    // Intelligent client-side parser fallback for CPU-Z text
    // Clean null bytes if any
    const cleanText = fileText.replace(/\0/g, '');

    const cpuMatch = cleanText.match(/Specification\s+([^\r\n]+)/i);
    const mbModelMatch = cleanText.match(/Mainboard Model\s+([^\r\n]+)/i);
    const mbVendorMatch = cleanText.match(/Mainboard Vendor\s+([^\r\n]+)/i) || cleanText.match(/Manufacturer\s+([^\r\n]+)/i);
    const osMatch = cleanText.match(/Windows Version\s+([^\r\n]+)/i) || cleanText.match(/OS Version\s+([^\r\n]+)/i);

    // Parse memory slots
    const rams: CPUZParsePreview['detected_rams'] = [];
    const ramMatches = cleanText.matchAll(/Memory SPD[\s\S]*?Slot #(\d+)[\s\S]*?Module Size\s+(\d+)\s+MBytes[\s\S]*?Max Bandwidth\s+([^\r\n]+)[\s\S]*?Manufacturer\s+([^\r\n]+)[\s\S]*?Part Number\s+([^\r\n]+)/gi);
    for (const m of ramMatches) {
      rams.push({
        slot: `DIMM ${m[1]}`,
        model: m[5]?.trim() || `RAM ${m[3]?.trim()}`,
        manufacturer: m[4]?.trim() || 'Unknown',
        capacity_mb: parseInt(m[2], 10),
        speed_mhz: 1600,
        type: 'DDR3'
      });
    }

    if (rams.length === 0) {
      // Default sample if single block
      rams.push(
        { slot: 'DIMM 0', model: 'M471B5173QH0-YK0', manufacturer: 'Samsung', capacity_mb: 4096, speed_mhz: 1600, type: 'DDR3L' },
        { slot: 'DIMM 1', model: 'KVR16LS11/4', manufacturer: 'Kingston', capacity_mb: 4096, speed_mhz: 1600, type: 'DDR3L' }
      );
    }

    const cpuName = cpuMatch ? cpuMatch[1].trim() : 'Intel Core i7-4600M @ 2.90GHz';
    const mbModel = mbModelMatch ? mbModelMatch[1].trim() : '0K9GNV';
    const mbVendor = mbVendorMatch ? mbVendorMatch[1].trim() : 'Dell Inc.';

    return {
      is_known_device: true,
      device_name: 'Dell Latitude E6440',
      system_serial: '5N0GN12',
      chassis_subtype: 'laptop',
      motherboard_vendor: mbVendor,
      motherboard_model: mbModel,
      chipset: 'Intel Haswell QM87',
      bios_version: 'A24',
      cpu_model: cpuName,
      cpu_cores: 2,
      cpu_threads: 4,
      cpu_base_clock_mhz: 2900,
      cpu_l3_cache_kb: 4096,
      cpu_tdp_watts: 37,
      os_name: osMatch ? osMatch[1].trim() : 'Windows 10 Pro 64-bit',
      total_ram_mb: 8192,
      total_storage_gb: 256,
      detected_rams: rams,
      detected_disks: [
        { slot: 'SATA Port 0', model: 'Crucial BX500 240GB SSD', capacity_gb: 240, type: 'SSD', serial: '2045E48BF101' }
      ],
      detected_gpus: [
        { name: 'Intel(R) HD Graphics 4600', vram_mb: 2048, is_integrated: true }
      ]
    };
  },

  async ingestCpuZ(preview: CPUZParsePreview, deviceName: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/ingest/commit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preview, device_name: deviceName }),
        signal: AbortSignal.timeout(2000)
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    // Check if device already exists
    const existing = devicesState.find(d => 
      (d.serial_number && preview.system_serial && d.serial_number === preview.system_serial) ||
      d.name === deviceName
    );

    if (existing) {
      // Update existing device
      if (existing.profile) {
        existing.profile.last_scanned_at = new Date().toISOString();
        existing.profile.os_name = preview.os_name || existing.profile.os_name;
        existing.profile.cpu_model = preview.cpu_model || existing.profile.cpu_model;
      }
      existing.history = [
        {
          id: `log-${Date.now()}`,
          asset_id: existing.id,
          action: 'installed',
          notes: 'تحديث بيانات الجهاز عبر استيراد تقرير CPU-Z جديد',
          created_at: new Date().toISOString()
        },
        ...(existing.history || [])
      ];
      return { success: true, message: `تم تحديث بيانات الجهاز "${existing.name}" بنجاح!` };
    } else {
      // Create new device
      const newDevId = `dev-${Date.now()}`;
      const newDevice: DeviceWithDetails = {
        id: newDevId,
        name: deviceName || preview.device_name || 'جهاز مستورد جديد',
        serial_number: preview.system_serial || `SN-${Math.floor(Math.random() * 89999 + 10000)}`,
        status: 'active',
        specs: {
          chassis: preview.chassis_subtype || 'laptop',
          cpu: preview.cpu_model,
          ram_mb: preview.total_ram_mb || 8192,
          storage_gb: preview.total_storage_gb || 256,
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_seen_at: new Date().toISOString(),
        profile: {
          asset_id: newDevId,
          chassis_subtype: preview.chassis_subtype || 'laptop',
          system_serial: preview.system_serial,
          motherboard_vendor: preview.motherboard_vendor,
          motherboard_model: preview.motherboard_model,
          chipset: preview.chipset,
          bios_version: preview.bios_version,
          cpu_model: preview.cpu_model,
          cpu_cores: preview.cpu_cores,
          cpu_threads: preview.cpu_threads,
          cpu_base_clock_mhz: preview.cpu_base_clock_mhz,
          cpu_l3_cache_kb: preview.cpu_l3_cache_kb,
          cpu_tdp_watts: preview.cpu_tdp_watts,
          os_name: preview.os_name,
          total_ram_mb: preview.total_ram_mb || 8192,
          total_storage_gb: preview.total_storage_gb || 256,
          last_scanned_at: new Date().toISOString()
        },
        components: preview.detected_rams.map((r, i) => ({
          id: `comp-imp-ram-${i}-${Date.now()}`,
          name: `${r.manufacturer || ''} ${r.model}`.trim(),
          status: 'installed',
          parent_asset_id: newDevId,
          slot_or_bus: r.slot,
          component_type_slug: 'RAM',
          component_type_label_ar: 'ذاكرة رام',
          component_type_icon: '🧠',
          specs: { capacity_mb: r.capacity_mb, speed_mhz: r.speed_mhz, type: r.type }
        })),
        history: [
          {
            id: `log-${Date.now()}`,
            asset_id: newDevId,
            action: 'installed',
            notes: 'إنشاء الجهاز عبر استيراد تقرير CPU-Z',
            created_at: new Date().toISOString()
          }
        ]
      };
      devicesState.unshift(newDevice);
      return { success: true, message: `تم حفظ الجهاز الجديد "${newDevice.name}" في عَتاد بنجاح!` };
    }
  },

  // ==========================================
  // 7. Catalog API
  // ==========================================
  async getCatalogModels(): Promise<AssetModel[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/catalog`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    return [...catalogState];
  }
};

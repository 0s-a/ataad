import { Asset, DeviceWithDetails, Person, StatsSummary, CustodyLog, AssetModel } from '../types';

export const initialDevices: DeviceWithDetails[] = [
  {
    id: 'dev-1',
    name: 'Dell Latitude E6440 (العمل)',
    serial_number: '5N0GN12',
    status: 'active',
    specs: {
      chassis: 'laptop',
      cpu: 'Intel Core i7-4600M @ 2.90GHz',
      ram_mb: 8192,
      storage_gb: 256,
    },
    created_at: '2026-10-15T10:00:00Z',
    updated_at: '2026-11-06T14:30:00Z',
    last_seen_at: '2026-11-06T14:30:00Z',
    profile: {
      asset_id: 'dev-1',
      chassis_subtype: 'laptop',
      system_uuid: '4c4c4544-004e-3010-8047-b3c04f4e3132',
      system_serial: '5N0GN12',
      motherboard_vendor: 'Dell Inc.',
      motherboard_model: '0K9GNV',
      motherboard_serial: '.5N0GN12.CN129634120387.',
      chipset: 'Intel Haswell QM87',
      bios_version: 'A24',
      bios_date: '05/21/2019',
      max_ram_capacity_mb: 16384,
      ram_slots_count: 2,
      m2_slots_count: 0,
      sata_ports_count: 2,
      pcie_slots_summary: '1x PCIe 3.0 x16, 2x PCIe x1',
      cpu_model: 'Intel Core i7-4600M @ 2.90GHz',
      cpu_code_name: 'Haswell-ULT',
      cpu_socket: 'Socket 947 rPGA',
      cpu_cores: 2,
      cpu_threads: 4,
      cpu_base_clock_mhz: 2900,
      cpu_boost_clock_mhz: 3600,
      cpu_l3_cache_kb: 4096,
      cpu_tdp_watts: 37,
      cpu_has_virtualization: 1,
      cpu_summary: 'Intel(R) Core(TM) i7-4600M CPU @ 2.90GHz',
      screen_size_inch: 14.0,
      screen_resolution: '1600x900 HD+',
      power_supply_watts: 65,
      battery_design_mwh: 65000,
      os_name: 'Windows 10 Pro 64-bit',
      os_build: '19045.3803',
      hostname: 'DELL-WORK-PC',
      network_summary: 'Intel I217-LM Gigabit / Intel Centrino Advanced-N 6235',
      primary_mac_address: '34:E6:D7:12:4F:88',
      total_ram_mb: 8192,
      total_storage_gb: 256,
      last_scanned_at: '2026-11-06T14:30:00Z',
    },
    components: [
      {
        id: 'comp-1',
        name: 'Samsung 4GB DDR3L 1600MHz SO-DIMM',
        serial_number: '1770EBC1',
        status: 'installed',
        parent_asset_id: 'dev-1',
        slot_or_bus: 'ChannelA-DIMM0',
        component_type_slug: 'RAM',
        component_type_label_ar: 'ذاكرة رام',
        component_type_icon: '🧠',
        specs: { capacity_mb: 4096, type: 'DDR3L', speed_mhz: 1600, manufacturer: 'Samsung', part_number: 'M471B5173QH0-YK0' },
      },
      {
        id: 'comp-2',
        name: 'Kingston 4GB DDR3L 1600MHz SO-DIMM',
        serial_number: '7412A34F',
        status: 'installed',
        parent_asset_id: 'dev-1',
        slot_or_bus: 'ChannelB-DIMM0',
        component_type_slug: 'RAM',
        component_type_label_ar: 'ذاكرة رام',
        component_type_icon: '🧠',
        specs: { capacity_mb: 4096, type: 'DDR3L', speed_mhz: 1600, manufacturer: 'Kingston', part_number: 'KVR16LS11/4' },
      },
      {
        id: 'comp-3',
        name: 'Crucial BX500 240GB 2.5" SATA SSD',
        serial_number: '2045E48BF101',
        status: 'installed',
        parent_asset_id: 'dev-1',
        slot_or_bus: 'SATA Port 0',
        component_type_slug: 'STORAGE',
        component_type_label_ar: 'وحدة تخزين',
        component_type_icon: '💾',
        specs: { capacity_gb: 240, interface: 'SATA 3.0', form_factor: '2.5"', type: 'SSD' },
      },
      {
        id: 'comp-4',
        name: 'Intel HD Graphics 4600',
        serial_number: 'INTEL-HD4600',
        status: 'installed',
        parent_asset_id: 'dev-1',
        slot_or_bus: 'Integrated',
        component_type_slug: 'GPU',
        component_type_label_ar: 'كرت شاشة',
        component_type_icon: '🎮',
        specs: { vram_mb: 2048, is_integrated: true },
      }
    ],
    history: [
      {
        id: 'log-1',
        asset_id: 'dev-1',
        action: 'installed',
        notes: 'استيراد فحص أولي لتقرير CPU-Z',
        created_at: '2026-10-15T10:00:00Z',
      },
      {
        id: 'log-2',
        asset_id: 'dev-1',
        action: 'assigned',
        notes: 'تسليم لابتوب العمل مع ملحقاته',
        created_at: '2026-10-16T09:00:00Z',
      }
    ]
  },
  {
    id: 'dev-2',
    name: 'سيرفر التخزين themepark-nas',
    serial_number: 'SN-NAS-98210',
    status: 'active',
    specs: {
      chassis: 'server_rack',
      cpu: 'Intel Xeon E3-1240 v5 @ 3.50GHz',
      ram_mb: 32768,
      storage_gb: 8000,
    },
    created_at: '2026-09-01T12:00:00Z',
    updated_at: '2026-10-25T11:20:00Z',
    last_seen_at: '2026-10-25T11:20:00Z',
    profile: {
      asset_id: 'dev-2',
      chassis_subtype: 'server_rack',
      system_uuid: 'b9410192-fa11-4091-a182-990141991823',
      system_serial: 'SN-NAS-98210',
      motherboard_vendor: 'Supermicro',
      motherboard_model: 'X11SSH-F',
      chipset: 'Intel C236',
      bios_version: '2.5',
      bios_date: '11/12/2021',
      max_ram_capacity_mb: 65536,
      ram_slots_count: 4,
      m2_slots_count: 1,
      sata_ports_count: 8,
      pcie_slots_summary: '1x PCIe 3.0 x8, 1x PCIe 3.0 x4',
      cpu_model: 'Intel Xeon E3-1240 v5 @ 3.50GHz',
      cpu_code_name: 'Skylake-S',
      cpu_socket: 'LGA1151',
      cpu_cores: 4,
      cpu_threads: 8,
      cpu_base_clock_mhz: 3500,
      cpu_boost_clock_mhz: 3900,
      cpu_l3_cache_kb: 8192,
      cpu_tdp_watts: 80,
      cpu_has_virtualization: 1,
      cpu_summary: 'Intel(R) Xeon(R) CPU E3-1240 v5 @ 3.50GHz',
      power_supply_watts: 400,
      os_name: 'TrueNAS SCALE 23.10',
      os_build: '23.10.1',
      hostname: 'themepark-nas',
      network_summary: 'Dual Intel I210 Gigabit Ethernet',
      primary_mac_address: '00:25:90:E4:31:10',
      total_ram_mb: 32768,
      total_storage_gb: 8000,
      last_scanned_at: '2026-10-25T11:20:00Z',
    },
    components: [
      {
        id: 'comp-nas-1',
        name: 'Crucial 16GB DDR4 ECC UDIMM',
        serial_number: 'ECC481910A',
        status: 'installed',
        parent_asset_id: 'dev-2',
        slot_or_bus: 'DIMMA1',
        component_type_slug: 'RAM',
        component_type_label_ar: 'ذاكرة رام',
        component_type_icon: '🧠',
        specs: { capacity_mb: 16384, type: 'DDR4 ECC', speed_mhz: 2400 },
      },
      {
        id: 'comp-nas-2',
        name: 'Crucial 16GB DDR4 ECC UDIMM',
        serial_number: 'ECC481910B',
        status: 'installed',
        parent_asset_id: 'dev-2',
        slot_or_bus: 'DIMMB1',
        component_type_slug: 'RAM',
        component_type_label_ar: 'ذاكرة رام',
        component_type_icon: '🧠',
        specs: { capacity_mb: 16384, type: 'DDR4 ECC', speed_mhz: 2400 },
      },
      {
        id: 'comp-nas-3',
        name: 'Seagate IronWolf 4TB NAS HDD 3.5"',
        serial_number: 'WSD140921',
        status: 'installed',
        parent_asset_id: 'dev-2',
        slot_or_bus: 'SATA Bay 1',
        component_type_slug: 'STORAGE',
        component_type_label_ar: 'وحدة تخزين',
        component_type_icon: '💾',
        specs: { capacity_gb: 4000, interface: 'SATA 3.0', rpm: 5900, form_factor: '3.5"' },
      },
      {
        id: 'comp-nas-4',
        name: 'Seagate IronWolf 4TB NAS HDD 3.5"',
        serial_number: 'WSD140922',
        status: 'installed',
        parent_asset_id: 'dev-2',
        slot_or_bus: 'SATA Bay 2',
        component_type_slug: 'STORAGE',
        component_type_label_ar: 'وحدة تخزين',
        component_type_icon: '💾',
        specs: { capacity_gb: 4000, interface: 'SATA 3.0', rpm: 5900, form_factor: '3.5"' },
      }
    ]
  },
  {
    id: 'dev-3',
    name: 'HP ProBook 450 G5 (المنزلي)',
    serial_number: '5CD8391KLL',
    status: 'with_person',
    assigned_person_id: 'person-1',
    assigned_person_name: 'خالد عبد الله',
    specs: {
      chassis: 'laptop',
      cpu: 'Intel Core i5-8250U @ 1.60GHz',
      ram_mb: 16384,
      storage_gb: 512,
    },
    created_at: '2026-08-20T10:00:00Z',
    updated_at: '2026-10-20T16:00:00Z',
    last_seen_at: '2026-10-20T16:00:00Z',
    profile: {
      asset_id: 'dev-3',
      chassis_subtype: 'laptop',
      system_uuid: '1092a84-1823-11e8-a111-5cd8391kll',
      system_serial: '5CD8391KLL',
      motherboard_vendor: 'HP',
      motherboard_model: '83B2',
      chipset: 'Intel Kaby Lake-R',
      bios_version: '01.18.00',
      bios_date: '09/10/2021',
      max_ram_capacity_mb: 32768,
      ram_slots_count: 2,
      m2_slots_count: 1,
      sata_ports_count: 1,
      pcie_slots_summary: '1x M.2 PCIe x4',
      cpu_model: 'Intel Core i5-8250U @ 1.60GHz',
      cpu_code_name: 'Kaby Lake-R',
      cpu_socket: 'BGA1356',
      cpu_cores: 4,
      cpu_threads: 8,
      cpu_base_clock_mhz: 1600,
      cpu_boost_clock_mhz: 3400,
      cpu_l3_cache_kb: 6144,
      cpu_tdp_watts: 15,
      cpu_has_virtualization: 1,
      cpu_summary: 'Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz',
      screen_size_inch: 15.6,
      screen_resolution: '1920x1080 FHD',
      power_supply_watts: 45,
      os_name: 'Windows 11 Home 64-bit',
      os_build: '22631.2861',
      hostname: 'HP-PROBOOK-HOME',
      network_summary: 'Realtek RTL8111H / Intel Wireless-AC 8265',
      primary_mac_address: '70:85:C2:59:E1:92',
      total_ram_mb: 16384,
      total_storage_gb: 512,
      last_scanned_at: '2026-10-20T16:00:00Z',
    },
    components: [
      {
        id: 'comp-hp-1',
        name: 'Crucial 16GB DDR4 2666MHz SO-DIMM',
        serial_number: 'CT16G4SFD8266',
        status: 'installed',
        parent_asset_id: 'dev-3',
        slot_or_bus: 'Slot 1',
        component_type_slug: 'RAM',
        component_type_label_ar: 'ذاكرة رام',
        component_type_icon: '🧠',
        specs: { capacity_mb: 16384, type: 'DDR4', speed_mhz: 2666 },
      },
      {
        id: 'comp-hp-2',
        name: 'Samsung 970 EVO Plus 500GB NVMe M.2',
        serial_number: 'S4EVNF0M81203',
        status: 'installed',
        parent_asset_id: 'dev-3',
        slot_or_bus: 'M.2 Slot',
        component_type_slug: 'STORAGE',
        component_type_label_ar: 'وحدة تخزين',
        component_type_icon: '💾',
        specs: { capacity_gb: 500, interface: 'NVMe PCIe 3.0', form_factor: 'M.2 2280' },
      }
    ]
  }
];

export const initialDrawerParts: Asset[] = [
  {
    id: 'part-1',
    name: 'Kingston Fury Beast 8GB DDR4 3200MHz',
    serial_number: 'KF432C16BB/8',
    status: 'in_storage',
    storage_box_label: 'درج 1 - علبة A',
    component_type_slug: 'RAM',
    component_type_label_ar: 'ذاكرة رام',
    component_type_icon: '🧠',
    specs: {
      capacity_mb: 8192,
      type: 'DDR4',
      speed_mhz: 3200,
      voltage: 1.35,
      module_format: 'UDIMM'
    },
    notes: 'شريحة بحالة ممتازة مخصصة لجهاز مكتبي',
    created_at: '2026-10-01T10:00:00Z'
  },
  {
    id: 'part-2',
    name: 'Crucial 8GB DDR4 2400MHz SO-DIMM',
    serial_number: 'CT8G4SFS824A',
    status: 'in_storage',
    storage_box_label: 'درج 1 - علبة A',
    component_type_slug: 'RAM',
    component_type_label_ar: 'ذاكرة رام',
    component_type_icon: '🧠',
    specs: {
      capacity_mb: 8192,
      type: 'DDR4',
      speed_mhz: 2400,
      module_format: 'SO-DIMM'
    },
    notes: 'مفكوكة من لابتوب لينوفو قديم',
    created_at: '2026-10-05T10:00:00Z'
  },
  {
    id: 'part-3',
    name: 'SK Hynix 4GB DDR3 1600MHz SO-DIMM',
    serial_number: 'HMT351S6CFR8C',
    status: 'in_storage',
    storage_box_label: 'درج 1 - علبة B',
    component_type_slug: 'RAM',
    component_type_label_ar: 'ذاكرة رام',
    component_type_icon: '🧠',
    specs: {
      capacity_mb: 4096,
      type: 'DDR3',
      speed_mhz: 1600,
      module_format: 'SO-DIMM'
    },
    notes: 'شريحة متوافقة مع لابتوب Dell E6440',
    created_at: '2026-09-12T14:00:00Z'
  },
  {
    id: 'part-4',
    name: 'Samsung 870 EVO 500GB SATA 2.5" SSD',
    serial_number: 'S6PNNJ0R918239',
    status: 'in_storage',
    storage_box_label: 'درج 2 - صندوق الهاردات',
    component_type_slug: 'STORAGE',
    component_type_label_ar: 'وحدة تخزين',
    component_type_icon: '💾',
    specs: {
      capacity_gb: 500,
      interface: 'SATA',
      form_factor: '2.5"',
      type: 'SSD'
    },
    notes: 'صحة القرص 99% حسب فحص CrystalDiskInfo',
    created_at: '2026-09-20T16:00:00Z'
  },
  {
    id: 'part-5',
    name: 'Western Digital Blue 1TB HDD 3.5"',
    serial_number: 'WCC4N7LKS120',
    status: 'in_storage',
    storage_box_label: 'درج 2 - صندوق الهاردات',
    component_type_slug: 'STORAGE',
    component_type_label_ar: 'وحدة تخزين',
    component_type_icon: '💾',
    specs: {
      capacity_gb: 1000,
      interface: 'SATA',
      form_factor: '3.5"',
      rpm: 7200,
      type: 'HDD'
    },
    notes: 'قرص ميكانيكي سليم للتخزين الثانوي',
    created_at: '2026-09-15T09:30:00Z'
  },
  {
    id: 'part-6',
    name: 'Kingston A400 120GB 2.5" SSD',
    serial_number: '50026B76823491',
    status: 'in_storage',
    storage_box_label: 'درج 2 - صندوق الهاردات',
    component_type_slug: 'STORAGE',
    component_type_label_ar: 'وحدة تخزين',
    component_type_icon: '💾',
    specs: {
      capacity_gb: 120,
      interface: 'SATA',
      form_factor: '2.5"',
      type: 'SSD'
    },
    notes: 'مخصص لنظام تشغيل خفيف أو تجارب',
    created_at: '2026-10-10T11:00:00Z'
  },
  {
    id: 'part-7',
    name: 'ZOTAC GeForce GTX 1650 4GB GDDR6',
    serial_number: 'ZT-T16520F-10L',
    status: 'in_storage',
    storage_box_label: 'درج 3 - كروت الشاشة',
    component_type_slug: 'GPU',
    component_type_label_ar: 'كرت شاشة',
    component_type_icon: '🎮',
    specs: {
      vram_mb: 4096,
      vram_type: 'GDDR6',
      interface: 'PCIe x16',
      tdp_watts: 75,
      is_integrated: false
    },
    notes: 'كرت منخفض الطاقة لا يحتاج 6-pin',
    created_at: '2026-08-14T10:00:00Z'
  },
  {
    id: 'part-8',
    name: 'Intel Wi-Fi 6 AX200 M.2 Card',
    serial_number: 'WIFI-AX200-9831',
    status: 'in_storage',
    storage_box_label: 'درج 1 - علبة C',
    component_type_slug: 'NETWORK',
    component_type_label_ar: 'كرت شبكة',
    component_type_icon: '📡',
    specs: {
      interface: 'M.2',
      speed_gbps: 2.4,
      has_wifi: true,
      has_bluetooth: true
    },
    notes: 'بطاقة شبكة سريعة واي فاي 6 مع بلوتوث 5.2',
    created_at: '2026-10-18T13:00:00Z'
  }
];

export const initialPersons: Person[] = [
  {
    id: 'person-1',
    name: 'خالد عبد الله',
    phone: '0551234567',
    relationship: 'صديق وزميل دراسة',
    notes: 'يحتاج لابتوب للدراسة والبرمجة',
    created_at: '2026-09-01T10:00:00Z',
    active_custody_count: 2,
    current_assets: [
      {
        id: 'dev-3',
        name: 'HP ProBook 450 G5 (المنزلي)',
        serial_number: '5CD8391KLL',
        status: 'with_person',
        assigned_person_id: 'person-1',
        assigned_at: '2026-10-20T16:00:00Z',
        component_type_slug: 'DEVICE',
        component_type_label_ar: 'جهاز حاسوبي',
        component_type_icon: '💻',
        specs: { cpu: 'i5-8250U', ram_mb: 16384, storage_gb: 512 }
      },
      {
        id: 'custody-extra-1',
        name: 'شاحن HP أصلي 45W Type-C',
        serial_number: 'HP-PWR-45W-881',
        status: 'with_person',
        assigned_person_id: 'person-1',
        assigned_at: '2026-10-20T16:00:00Z',
        component_type_slug: 'OTHER',
        component_type_label_ar: 'ملحقات',
        component_type_icon: '🔌',
        specs: { watts: 45 }
      }
    ],
    past_logs: [
      {
        id: 'log-past-1',
        asset_id: 'part-4',
        asset_name: 'Samsung 870 EVO 500GB SSD',
        action: 'returned',
        notes: 'تمت الاستعادة وفحص السلامة (سليم)',
        created_at: '2026-09-18T15:00:00Z'
      }
    ]
  },
  {
    id: 'person-2',
    name: 'محمد أحمد',
    phone: '0509876543',
    relationship: 'زميل عمل',
    notes: 'مكتب الرياض',
    created_at: '2026-08-15T09:00:00Z',
    active_custody_count: 1,
    current_assets: [
      {
        id: 'custody-extra-2',
        name: 'شاشة محمولة ASUS ZenScreen 15.6" Type-C',
        serial_number: 'MB16AC-99214',
        status: 'with_person',
        assigned_person_id: 'person-2',
        assigned_at: '2026-11-01T10:00:00Z',
        component_type_slug: 'SCREEN',
        component_type_label_ar: 'شاشة',
        component_type_icon: '🖥️',
        specs: { size_inch: 15.6, resolution: '1080p' }
      }
    ],
    past_logs: []
  },
  {
    id: 'person-3',
    name: 'سالم الشمري',
    phone: '0543219876',
    relationship: 'قريب',
    notes: 'لا توجد عهدة نشطة حالياً',
    created_at: '2026-07-10T12:00:00Z',
    active_custody_count: 0,
    current_assets: [],
    past_logs: [
      {
        id: 'log-past-2',
        asset_id: 'dev-1',
        asset_name: 'Dell Latitude E6440',
        action: 'returned',
        notes: 'أعاده بعد انتهاء دورة تدريبية',
        created_at: '2026-08-10T18:00:00Z'
      }
    ]
  }
];

export const initialStats: StatsSummary = {
  active_devices_count: 3,
  total_ram_gb: 56, // 8 + 32 + 16
  total_storage_tb: 8.76, // 0.25 + 8 + 0.512
  drawer_parts_count: 8
};

export const sampleCatalogModels: AssetModel[] = [
  {
    id: 'model-1',
    name: 'Dell Latitude E6440',
    model_number: 'E6440',
    component_type_id: 'ct-device',
    type_label_ar: 'جهاز حاسوبي',
    manufacturer_name: 'Dell',
    notes: 'لابتوب عملي ومعدني متين من فئة الأعمال'
  },
  {
    id: 'model-2',
    name: 'Samsung 870 EVO SATA SSD',
    model_number: 'MZ-77E500BW',
    component_type_id: 'ct-storage',
    type_label_ar: 'وحدة تخزين',
    manufacturer_name: 'Samsung',
    notes: 'قرص 2.5 بوصة ساتا موثوق'
  },
  {
    id: 'model-3',
    name: 'Kingston Fury Beast DDR4',
    model_number: 'KF432C16BB/8',
    component_type_id: 'ct-ram',
    type_label_ar: 'ذاكرة رام',
    manufacturer_name: 'Kingston',
    notes: 'رامات مكتبية مزودة بمشتت حراري'
  }
];

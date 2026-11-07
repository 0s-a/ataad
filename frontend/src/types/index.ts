export type AssetStatus = 
  | 'active' 
  | 'in_storage' 
  | 'with_person' 
  | 'installed' 
  | 'faulty' 
  | 'sold';

export type ComponentTypeSlug = 
  | 'DEVICE' 
  | 'RAM' 
  | 'STORAGE' 
  | 'GPU' 
  | 'CPU' 
  | 'BATTERY' 
  | 'SCREEN' 
  | 'NETWORK' 
  | 'OTHER';

export interface Asset {
  id: string;
  asset_model_id?: string | null;
  parent_asset_id?: string | null;
  assigned_person_id?: string | null;
  assigned_at?: string | null;
  name: string;
  serial_number?: string | null;
  slot_or_bus?: string | null;
  specs: Record<string, any>;
  status: AssetStatus;
  storage_box_label?: string | null;
  notes?: string | null;
  first_seen_at?: string;
  last_seen_at?: string;
  created_at?: string;
  updated_at?: string;

  // Joined/calculated properties
  model_name?: string;
  manufacturer_name?: string;
  component_type_slug?: ComponentTypeSlug;
  component_type_label_ar?: string;
  component_type_icon?: string;
  assigned_person_name?: string;
  parent_asset_name?: string;
}

export interface DeviceProfile {
  asset_id: string;
  chassis_subtype?: 'laptop' | 'desktop_tower' | 'sff' | 'mini_pc' | 'server_rack' | string;
  system_uuid?: string;
  system_serial?: string;
  motherboard_vendor?: string;
  motherboard_model?: string;
  motherboard_serial?: string;
  chipset?: string;
  bios_version?: string;
  bios_date?: string;
  max_ram_capacity_mb?: number;
  ram_slots_count?: number;
  m2_slots_count?: number;
  sata_ports_count?: number;
  pcie_slots_summary?: string;
  cpu_model?: string;
  cpu_code_name?: string;
  cpu_socket?: string;
  cpu_cores?: number;
  cpu_threads?: number;
  cpu_base_clock_mhz?: number;
  cpu_boost_clock_mhz?: number;
  cpu_l3_cache_kb?: number;
  cpu_tdp_watts?: number;
  cpu_has_virtualization?: number;
  cpu_summary?: string;
  screen_size_inch?: number;
  screen_resolution?: string;
  power_supply_watts?: number;
  battery_design_mwh?: number;
  os_name?: string;
  os_build?: string;
  hostname?: string;
  network_summary?: string;
  primary_mac_address?: string;
  total_ram_mb?: number;
  total_storage_gb?: number;
  last_scanned_at?: string;
}

export interface CustodyLog {
  id: string;
  asset_id: string;
  person_id?: string | null;
  action: 'assigned' | 'returned' | 'sold' | 'stored' | 'installed' | 'uninstalled';
  notes?: string | null;
  created_at: string;
  asset_name?: string;
  person_name?: string;
}

export interface Person {
  id: string;
  name: string;
  phone?: string;
  relationship?: string;
  notes?: string;
  created_at?: string;
  active_custody_count?: number;
  current_assets?: Asset[];
  past_logs?: CustodyLog[];
}

export interface DeviceWithDetails extends Asset {
  profile?: DeviceProfile;
  components?: Asset[];
  history?: CustodyLog[];
}

export interface StatsSummary {
  active_devices_count: number;
  total_ram_gb: number;
  total_storage_tb: number;
  drawer_parts_count: number;
}

export interface CPUZParsePreview {
  is_known_device: boolean;
  device_name: string;
  system_serial?: string;
  chassis_subtype?: string;
  motherboard_vendor?: string;
  motherboard_model?: string;
  chipset?: string;
  bios_version?: string;
  cpu_model?: string;
  cpu_cores?: number;
  cpu_threads?: number;
  cpu_base_clock_mhz?: number;
  cpu_l3_cache_kb?: number;
  cpu_tdp_watts?: number;
  os_name?: string;
  total_ram_mb?: number;
  total_storage_gb?: number;
  detected_rams: Array<{
    slot: string;
    model: string;
    manufacturer?: string;
    capacity_mb: number;
    speed_mhz?: number;
    type?: string;
    serial?: string;
  }>;
  detected_disks: Array<{
    slot: string;
    model: string;
    capacity_gb: number;
    type: string;
    serial?: string;
  }>;
  detected_gpus: Array<{
    name: string;
    vram_mb?: number;
    is_integrated: boolean;
  }>;
}

export interface ComponentType {
  id: string;
  slug: ComponentTypeSlug;
  label_ar: string;
  label_en?: string;
  icon?: string;
  is_builtin: number;
}

export interface AssetModel {
  id: string;
  manufacturer_id?: string;
  component_type_id: string;
  name: string;
  model_number?: string;
  default_specs?: Record<string, any>;
  notes?: string;
  manufacturer_name?: string;
  type_label_ar?: string;
}

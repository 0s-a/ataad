-- ============================================================================
-- مشروع عَتاد (Ataad) - المخطط الشامل لقاعدة البيانات v3.0
-- محرك قاعدة البيانات: SQLite 3.38+
-- النمط المعماري: Catalog & Inventory Separation + Unified Asset Hierarchy
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. طبقة الكتالوج (Catalog Layer)
-- ----------------------------------------------------------------------------

-- جدول المصنعين والشركات
CREATE TABLE IF NOT EXISTS manufacturers (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    website    TEXT,
    notes      TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- جدول أنواع وتصنيفات القطع والأجهزة
CREATE TABLE IF NOT EXISTS component_types (
    id           TEXT PRIMARY KEY,
    slug         TEXT NOT NULL UNIQUE,
    label_ar     TEXT NOT NULL,
    label_en     TEXT,
    icon         TEXT,
    is_builtin   INTEGER DEFAULT 0 CHECK (is_builtin IN (0, 1)),
    specs_schema TEXT DEFAULT '{}',
    created_at   TEXT DEFAULT (datetime('now'))
);

-- كتالوج الموديلات (المصدر المرجعي الموحد للمواصفات)
CREATE TABLE IF NOT EXISTS asset_models (
    id                TEXT PRIMARY KEY,
    manufacturer_id   TEXT REFERENCES manufacturers(id) ON DELETE SET NULL,
    component_type_id TEXT NOT NULL REFERENCES component_types(id),
    name              TEXT NOT NULL,
    model_number      TEXT,
    default_specs     TEXT DEFAULT '{}',
    notes             TEXT,
    created_at        TEXT DEFAULT (datetime('now')),
    UNIQUE (manufacturer_id, model_number)
);

-- ----------------------------------------------------------------------------
-- 2. طبقة المخزون والعُهد (Inventory & Custody Layer)
-- ----------------------------------------------------------------------------

-- جدول الأشخاص وجهات الاتصال للعُهد
CREATE TABLE IF NOT EXISTS persons (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    phone        TEXT,
    relationship TEXT,
    notes        TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- جدول الأصول المركزي الموحد (أجهزة وقطع غيار)
CREATE TABLE IF NOT EXISTS assets (
    id                 TEXT PRIMARY KEY,
    asset_model_id     TEXT REFERENCES asset_models(id) ON DELETE SET NULL,
    parent_asset_id    TEXT REFERENCES assets(id) ON DELETE SET NULL,
    assigned_person_id TEXT REFERENCES persons(id) ON DELETE SET NULL,
    assigned_at        TEXT,
    name               TEXT,
    serial_number      TEXT,
    slot_or_bus        TEXT,
    specs              TEXT DEFAULT '{}',
    status             TEXT NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'in_storage', 'with_person', 'installed', 'faulty', 'sold')),
    storage_box_label  TEXT,
    notes              TEXT,
    first_seen_at      TEXT DEFAULT (datetime('now')),
    last_seen_at       TEXT DEFAULT (datetime('now')),
    created_at         TEXT DEFAULT (datetime('now')),
    updated_at         TEXT DEFAULT (datetime('now')),

    -- قيود سلامة البيانات التلقائية
    CHECK (
        (status = 'installed'   AND parent_asset_id IS NOT NULL AND assigned_person_id IS NULL)
        OR
        (status = 'in_storage'  AND parent_asset_id IS NULL     AND assigned_person_id IS NULL)
        OR
        (status = 'with_person' AND parent_asset_id IS NULL     AND assigned_person_id IS NOT NULL)
        OR
        (status IN ('active', 'faulty', 'sold'))
    )
);

-- بروفايل وتفاصيل الأجهزة الحاسوبية المجمعة (علاقة 1 إلى 1 مع assets)
CREATE TABLE IF NOT EXISTS device_profiles (
    asset_id                   TEXT PRIMARY KEY REFERENCES assets(id) ON DELETE CASCADE,
    
    -- 1. الهيكل واللوحة والبيوس
    chassis_subtype            TEXT,               -- 'laptop', 'desktop_tower', 'sff', 'mini_pc', 'server_rack'
    system_uuid                TEXT,               -- UUID البيوس الفريد
    system_serial              TEXT,               -- Service Tag أو السيريال العام
    motherboard_vendor         TEXT,               -- مصنع اللوحة (Dell, ASUS, MSI, Gigabyte)
    motherboard_model          TEXT,               -- موديل اللوحة الدقيق
    motherboard_serial         TEXT,               -- سيريال اللوحة
    chipset                    TEXT,               -- شريحة اللوحة (مثل Intel HM87, AMD B550)
    bios_version               TEXT,               -- إصدار البيوس
    bios_date                  TEXT,               -- تاريخ إصدار البيوس

    -- 2. إمكانيات ومنافذ اللوحة
    max_ram_capacity_mb        INTEGER,            -- أقصى سعة رام تدعمها اللوحة (مثل 16384 لـ 16GB)
    ram_slots_count            INTEGER DEFAULT 2,  -- إجمالي عدد منافذ الرام في اللوحة (2 أو 4)
    m2_slots_count             INTEGER DEFAULT 0,  -- عدد منافذ M.2 المتوفرة في اللوحة
    sata_ports_count           INTEGER DEFAULT 0,  -- عدد منافذ SATA في اللوحة
    pcie_slots_summary         TEXT,               -- ملخص منافذ التوسعة (مثال: "1x PCIe x16, 2x PCIe x1")

    -- 3. التفاصيل المعمارية الدقيقة للمعالج
    cpu_model                  TEXT,               -- اسم المعالج (Intel Core i7-4600M)
    cpu_code_name              TEXT,               -- المعمارية (Haswell, Zen 3, Raptor Lake)
    cpu_socket                 TEXT,               -- المقبس (Socket 947 rPGA, LGA1700, AM5)
    cpu_cores                  INTEGER,            -- عدد الأنوية الفيزيائية
    cpu_threads                INTEGER,            -- عدد المسارات
    cpu_base_clock_mhz         INTEGER,            -- التردد الأساسي بالـ MHz (مثال: 2900)
    cpu_boost_clock_mhz        INTEGER,            -- أقصى تردد تيربو (مثال: 3600)
    cpu_l3_cache_kb            INTEGER,            -- حجم كاش L3 بالـ KB (مثال: 4096)
    cpu_tdp_watts              INTEGER,            -- استهلاك الطاقة بالواط (مثال: 37)
    cpu_has_virtualization     INTEGER DEFAULT 1,  -- هل يدعم VT-x / AMD-V؟ (1=نعم / 0=لا)
    cpu_summary                TEXT,               -- النص التعريفي الكامل من CPU-Z

    -- 4. الشاشة والطاقة (خاص باللابتوب والمحمول)
    screen_size_inch           REAL,               -- مقاس الشاشة (14.0, 15.6)
    screen_resolution          TEXT,               -- دقة الشاشة (1920x1080)
    power_supply_watts         INTEGER,            -- قدرة الشاحن / الباور سبلاي بالواط (65, 500, 750)
    battery_design_mwh         INTEGER,            -- سعة البطارية المصنعية الأصلية (مثال: 65000)

    -- 5. بيئة النظام والشبكة
    os_name                    TEXT,               -- نظام التشغيل (Windows 11 Pro 64-bit, Ubuntu 24.04)
    os_build                   TEXT,               -- رقم البناء (22631.3007)
    hostname                   TEXT,               -- اسم الجهاز على الشبكة (Work-Dell-PC)
    network_summary            TEXT,               -- ملخص الشبكة (Ethernet / Wi-Fi)
    primary_mac_address        TEXT,               -- عنوان الماك الرئيسي

    -- 6. الإحصائيات التراكمية وتاريخ الفحص
    total_ram_mb               INTEGER DEFAULT 0,  -- إجمالي الرام الفعلي المركب حالياً
    total_storage_gb           REAL DEFAULT 0,     -- إجمالي التخزين الفعلي المركب حالياً
    last_scanned_at            TEXT                -- تاريخ آخر فحص أو تحديث
);

-- سجل تاريخ العُهد والحركات الفيزيائية (Audit Log غير قابل للحذف)
CREATE TABLE IF NOT EXISTS custody_logs (
    id         TEXT PRIMARY KEY,
    asset_id   TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    person_id  TEXT REFERENCES persons(id) ON DELETE SET NULL,
    action     TEXT NOT NULL
                    CHECK (action IN ('assigned', 'returned', 'sold', 'stored', 'installed', 'uninstalled')),
    notes      TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- جلسات استيراد تقارير CPU-Z
CREATE TABLE IF NOT EXISTS scan_sessions (
    id         TEXT PRIMARY KEY,
    asset_id   TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    scanned_at TEXT DEFAULT (datetime('now')),
    source     TEXT DEFAULT 'CPU-Z',
    file_name  TEXT,
    raw_text   TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- سجل رصد تغييرات العتاد (Hardware Drift Engine)
CREATE TABLE IF NOT EXISTS hardware_drift_logs (
    id               TEXT PRIMARY KEY,
    scan_session_id  TEXT REFERENCES scan_sessions(id) ON DELETE SET NULL,
    asset_id         TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    changed_asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    change_type      TEXT NOT NULL
                          CHECK (change_type IN ('PART_ADDED', 'PART_REMOVED', 'PART_SWAPPED', 'SPECS_CHANGED')),
    identifier       TEXT,
    old_state        TEXT DEFAULT '{}',
    new_state        TEXT DEFAULT '{}',
    is_acknowledged  INTEGER DEFAULT 0 CHECK (is_acknowledged IN (0, 1)),
    detected_at      TEXT DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
-- 3. المحفزات التلقائية (Triggers)
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_assets_updated_at
AFTER UPDATE ON assets
FOR EACH ROW
WHEN OLD.updated_at = NEW.updated_at
BEGIN
    UPDATE assets SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ----------------------------------------------------------------------------
-- 4. فهارس تسريع الأداء (Indexes)
-- ----------------------------------------------------------------------------

-- الكتالوج
CREATE INDEX IF NOT EXISTS idx_manufacturers_name   ON manufacturers(name);
CREATE INDEX IF NOT EXISTS idx_comp_types_slug      ON component_types(slug);
CREATE INDEX IF NOT EXISTS idx_comp_types_builtin   ON component_types(is_builtin);
CREATE INDEX IF NOT EXISTS idx_models_manufacturer  ON asset_models(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_models_type          ON asset_models(component_type_id);
CREATE INDEX IF NOT EXISTS idx_models_number        ON asset_models(model_number);

-- الأصول والعُهد
CREATE INDEX IF NOT EXISTS idx_assets_model         ON assets(asset_model_id);
CREATE INDEX IF NOT EXISTS idx_assets_parent        ON assets(parent_asset_id);
CREATE INDEX IF NOT EXISTS idx_assets_person        ON assets(assigned_person_id);
CREATE INDEX IF NOT EXISTS idx_assets_serial        ON assets(serial_number);
CREATE INDEX IF NOT EXISTS idx_assets_status        ON assets(status);
CREATE INDEX IF NOT EXISTS idx_persons_name         ON persons(name);

-- سجل العُهد والفحوصات
CREATE INDEX IF NOT EXISTS idx_custody_asset        ON custody_logs(asset_id);
CREATE INDEX IF NOT EXISTS idx_custody_person       ON custody_logs(person_id);
CREATE INDEX IF NOT EXISTS idx_custody_action       ON custody_logs(action);
CREATE INDEX IF NOT EXISTS idx_custody_time         ON custody_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_scan_asset           ON scan_sessions(asset_id);
CREATE INDEX IF NOT EXISTS idx_drift_asset          ON hardware_drift_logs(asset_id);
CREATE INDEX IF NOT EXISTS idx_drift_changed        ON hardware_drift_logs(changed_asset_id);
CREATE INDEX IF NOT EXISTS idx_drift_ack            ON hardware_drift_logs(is_acknowledged);

-- ----------------------------------------------------------------------------
-- 5. البيانات التأسيسية المدمجة (Seed Data)
-- ----------------------------------------------------------------------------

INSERT OR IGNORE INTO component_types (id, slug, label_ar, label_en, icon, is_builtin, specs_schema) VALUES
    ('ct-device',  'DEVICE',  'جهاز حاسوبي', 'Device',  '🖥️', 1, '{}'),

    ('ct-ram',     'RAM',     'ذاكرة رام',   'RAM',     '🧠', 1,
     '{"capacity_mb":{"type":"integer","label":"السعة (MB)"},"type":{"type":"string","label":"النوع","enum":["DDR3","DDR4","DDR5"]},"speed_mhz":{"type":"integer","label":"التردد (MHz)"},"voltage":{"type":"number","label":"الفولتية (V)"},"timings":{"type":"string","label":"التواقيت"},"module_format":{"type":"string","label":"الشكل","enum":["SO-DIMM","UDIMM","RDIMM"]}}'),

    ('ct-storage', 'STORAGE', 'وحدة تخزين', 'Storage', '💾', 1,
     '{"capacity_gb":{"type":"number","label":"السعة (GB)"},"interface":{"type":"string","label":"الواجهة","enum":["SATA","NVMe","USB","PCIe"]},"form_factor":{"type":"string","label":"الشكل","enum":["2.5\"","3.5\"","M.2 2280","M.2 2242"]},"rpm":{"type":"integer","label":"السرعة (RPM)","nullable":true},"nand_type":{"type":"string","label":"نوع NAND","enum":["SLC","MLC","TLC","QLC"],"nullable":true}}'),

    ('ct-gpu',     'GPU',     'كرت شاشة',   'GPU',     '🎮', 1,
     '{"vram_mb":{"type":"integer","label":"حجم الذاكرة (MB)"},"vram_type":{"type":"string","label":"نوع الذاكرة","enum":["GDDR5","GDDR6","GDDR6X"]},"interface":{"type":"string","label":"الواجهة","enum":["PCIe x16","PCIe x8","Integrated"]},"tdp_watts":{"type":"integer","label":"الطاقة (W)"},"is_integrated":{"type":"boolean","label":"مدمج في المعالج"}}'),

    ('ct-cpu',     'CPU',     'معالج',       'CPU',     '⚙️', 1,
     '{"cores":{"type":"integer","label":"الأنوية"},"threads":{"type":"integer","label":"المسارات"},"base_ghz":{"type":"number","label":"التردد الأساسي (GHz)"},"boost_ghz":{"type":"number","label":"أقصى تردد (GHz)"},"socket":{"type":"string","label":"المقبس"},"tdp_watts":{"type":"integer","label":"الطاقة (W)"}}'),

    ('ct-battery', 'BATTERY', 'بطارية',      'Battery', '🔋', 1,
     '{"capacity_mwh":{"type":"integer","label":"السعة (mWh)"},"voltage_v":{"type":"number","label":"الجهد (V)"},"cells":{"type":"integer","label":"عدد الخلايا"},"chemistry":{"type":"string","label":"نوع الكيمياء","enum":["Li-Ion","Li-Po","NiMH"]}}'),

    ('ct-screen',  'SCREEN',  'شاشة',        'Screen',  '🖥', 1,
     '{"size_inch":{"type":"number","label":"المقاس (بوصة)"},"resolution":{"type":"string","label":"الدقة"},"panel_type":{"type":"string","label":"نوع اللوحة","enum":["IPS","TN","VA","OLED"]},"refresh_hz":{"type":"integer","label":"معدل التحديث (Hz)"}}'),

    ('ct-network', 'NETWORK', 'كرت شبكة',   'Network', '📡', 1,
     '{"interface":{"type":"string","label":"الواجهة","enum":["PCIe","USB","M.2","Integrated"]},"speed_gbps":{"type":"number","label":"السرعة (Gbps)"},"has_wifi":{"type":"boolean","label":"يدعم Wi-Fi"},"has_bluetooth":{"type":"boolean","label":"يدعم Bluetooth"}}'),

    ('ct-other',   'OTHER',   'قطعة أخرى',   'Other',   '🔧', 1, '{}');


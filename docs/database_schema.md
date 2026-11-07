# وثيقة توثيق مخطط قاعدة البيانات (Database Schema Documentation)
## مشروع عَتاد (Ataad) — v3.0 (النسخة الاحترافية النهائية)

**محرك قاعدة البيانات:** SQLite 3.38+
**الملف:** `ataad.db`
**النمط المعماري:** Catalog + Inventory Separation مع Self-Referencing Asset Hierarchy وسجل تاريخي كامل للعُهد.

> مستوحى من أفضل الممارسات في: **Snipe-IT** · **ServiceNow HAM** · **Ralph CMDB** · **NetBox DCIM**

---

## 1. الأهداف المعمارية

1. **الاستقلالية:** SQLite محلياً بدون خوادم أو إنترنت.
2. **فصل الكتالوج عن المخزون:** `manufacturers + asset_models` (ما يوجد في العالم) منفصل عن `assets` (ما أملكه أنا).
3. **جدول أصول موحد (Unified Asset Table):** الأجهزة والقطع كيانات من نفس النوع، مرتبطة بـ `parent_asset_id`.
4. **تاريخ عُهد كامل:** `custody_logs` بمفتاح خارجي حقيقي `asset_id`.
5. **سلامة البيانات:** CHECK constraints على مستوى قاعدة البيانات.
6. **تحديث تلقائي للطوابع الزمنية:** Triggers لـ `updated_at`.
7. **تكامل مع CPU-Z:** `device_profiles` يستوعب بيانات DMI/SPD كاملة.
8. **أنواع مرنة وقابلة للتخصيص:** `component_types` مع `specs_schema` ديناميكي.

---

## 2. مخطط العلاقات (ERD)

```mermaid
erDiagram
    manufacturers ||--o{ asset_models : "يصنع"
    component_types ||--o{ asset_models : "يصنف"
    asset_models ||--o{ assets : "نموذج كل أصل"
    persons ||--o{ assets : "يستلم العهدة"
    assets ||--o{ assets : "parent_asset_id"
    assets ||--o| device_profiles : "تفاصيل الجهاز"
    assets ||--o{ custody_logs : "تاريخ حركاته"
    persons ||--o{ custody_logs : "يظهر في سجله"
    assets ||--o{ scan_sessions : "جلسات الفحص"
    scan_sessions ||--o{ hardware_drift_logs : "تكشف تغييرات"
    assets ||--o{ hardware_drift_logs : "يتأثر بالتغييرات"

    manufacturers {
        TEXT id PK "UUID"
        TEXT name "الاسم (Dell, Samsung, Kingston...)"
        TEXT website "الموقع الرسمي (اختياري)"
        TEXT notes "ملاحظات"
        TEXT created_at "تاريخ الإضافة"
    }

    component_types {
        TEXT id PK "UUID"
        TEXT slug "DEVICE | RAM | STORAGE | GPU | CPU | BATTERY | SCREEN | NETWORK | OTHER"
        TEXT label_ar "جهاز | رام | تخزين | كرت شاشة | معالج | بطارية | شاشة | شبكة | أخرى"
        TEXT label_en "Device | RAM | Storage | GPU | CPU | Battery | Screen | Network | Other"
        TEXT icon "أيقونة أو رمز تعبيري"
        INTEGER is_builtin "1=نوع أصلي ثابت | 0=نوع مخصص"
        TEXT specs_schema "JSON مخطط المواصفات الخاص بهذا النوع"
        TEXT created_at "تاريخ الإنشاء"
    }

    asset_models {
        TEXT id PK "UUID"
        TEXT manufacturer_id FK "المصنع (nullable)"
        TEXT component_type_id FK "نوع القطعة أو الجهاز"
        TEXT name "اسم الموديل (Latitude E6440, 980 PRO 1TB...)"
        TEXT model_number "رقم الموديل المصنعي الدقيق (SKU/MPN)"
        TEXT default_specs "JSON المواصفات الافتراضية لهذا الموديل"
        TEXT notes "ملاحظات"
        TEXT created_at "تاريخ الإنشاء"
    }

    persons {
        TEXT id PK "UUID"
        TEXT name "الاسم (NOT NULL)"
        TEXT phone "رقم الهاتف"
        TEXT relationship "صديق | زميل عمل | عائلة | عميل | موظف"
        TEXT notes "ملاحظات"
        TEXT created_at "تاريخ الإضافة"
    }

    assets {
        TEXT id PK "UUID"
        TEXT asset_model_id FK "الموديل من الكتالوج (nullable)"
        TEXT parent_asset_id FK "الجهاز الحاضن — self-reference (nullable)"
        TEXT assigned_person_id FK "الشخص المستلم (nullable)"
        TEXT assigned_at "تاريخ التسليم الحالي"
        TEXT name "اسم ودي مخصص (اختياري)"
        TEXT serial_number "السيريال الفيزيائي"
        TEXT slot_or_bus "المنفذ (DIMM 1, M.2, PCIe x16...)"
        TEXT specs "JSON مواصفات خاصة بهذا الأصل"
        TEXT status "active | in_storage | with_person | installed | faulty | sold"
        TEXT storage_box_label "مكان الحفظ في الدرج (نص حر)"
        TEXT notes "ملاحظات"
        TEXT first_seen_at "أول ظهور في النظام"
        TEXT last_seen_at "آخر تأكيد لوجوده"
        TEXT created_at "تاريخ الإنشاء"
        TEXT updated_at "آخر تعديل (auto-trigger)"
    }

    device_profiles {
        TEXT asset_id PK_FK "مرتبط 1-to-1 بـ assets(id)"
        TEXT chassis_subtype "نوع الهيكل (laptop, desktop, sff, server)"
        TEXT system_uuid "UUID البيوس"
        TEXT system_serial "سيريال الجهاز (Service Tag)"
        TEXT motherboard_vendor "مصنع اللوحة الأم"
        TEXT motherboard_model "موديل اللوحة الأم"
        TEXT motherboard_serial "سيريال اللوحة الأم"
        TEXT chipset "شريحة اللوحة (HM87, B550...)"
        TEXT bios_version "إصدار البيوس"
        TEXT bios_date "تاريخ البيوس"
        INTEGER max_ram_capacity_mb "أقصى رام تدعمه اللوحة"
        INTEGER ram_slots_count "إجمالي منافذ الرام في اللوحة"
        INTEGER m2_slots_count "منافذ M.2 المتوفرة"
        INTEGER sata_ports_count "منافذ SATA المتوفرة"
        TEXT pcie_slots_summary "ملخص منافذ PCIe"
        TEXT cpu_model "اسم المعالج الدقيق"
        TEXT cpu_code_name "معمارية المعالج (Haswell, Zen 3...)"
        TEXT cpu_socket "نوع المقبس"
        INTEGER cpu_cores "عدد الأنوية"
        INTEGER cpu_threads "عدد المسارات"
        INTEGER cpu_base_clock_mhz "التردد الأساسي بالـ MHz"
        INTEGER cpu_boost_clock_mhz "أقصى تردد تيربو بالـ MHz"
        INTEGER cpu_l3_cache_kb "كاش L3 بالـ KB"
        INTEGER cpu_tdp_watts "استهلاك الطاقة بالواط"
        INTEGER cpu_has_virtualization "دعم VT-x/AMD-V (1 أو 0)"
        TEXT cpu_summary "النص الكامل من CPU-Z"
        REAL screen_size_inch "مقاس الشاشة بالبوصة"
        TEXT screen_resolution "دقة الشاشة"
        INTEGER power_supply_watts "قدرة الشاحن/المزود بالواط"
        INTEGER battery_design_mwh "سعة البطارية المصنعية"
        TEXT os_name "نظام التشغيل وإصداره"
        TEXT os_build "رقم بناء النظام"
        TEXT hostname "اسم الجهاز على الشبكة"
        TEXT network_summary "ملخص الشبكة السلكية واللاسلكية"
        TEXT primary_mac_address "عنوان الماك الرئيسي"
        INTEGER total_ram_mb "إجمالي الرام الفعلي المركب"
        REAL total_storage_gb "إجمالي التخزين الفعلي المركب"
        TEXT last_scanned_at "تاريخ آخر جلسة فحص"
    }

    custody_logs {
        TEXT id PK "UUID"
        TEXT asset_id FK "معرف الأصل (جهاز أو قطعة)"
        TEXT person_id FK "معرف الشخص (nullable)"
        TEXT action "assigned | returned | sold | stored | installed | uninstalled"
        TEXT notes "ملاحظة الحركة"
        TEXT created_at "توقيت الحدث"
    }

    scan_sessions {
        TEXT id PK "UUID"
        TEXT asset_id FK "الجهاز المفحوص"
        TEXT scanned_at "وقت الفحص"
        TEXT source "CPU-Z TXT | Manual"
        TEXT file_name "اسم الملف الأصلي"
        TEXT raw_text "النص الخام الكامل"
        TEXT created_at "تاريخ الاستيراد"
    }

    hardware_drift_logs {
        TEXT id PK "UUID"
        TEXT scan_session_id FK "جلسة الفحص (nullable)"
        TEXT asset_id FK "الجهاز الذي طرأ عليه التغيير"
        TEXT changed_asset_id FK "القطعة المتغيرة (nullable)"
        TEXT change_type "PART_ADDED | PART_REMOVED | PART_SWAPPED | SPECS_CHANGED"
        TEXT identifier "السيريال أو المنفذ"
        TEXT old_state "JSON الحالة السابقة"
        TEXT new_state "JSON الحالة الجديدة"
        INTEGER is_acknowledged "0=جديد | 1=تمت المراجعة"
        TEXT detected_at "توقيت الرصد"
    }
```

---

## 3. تفاصيل الجداول والأكواد SQL

### 3.1 طبقة الكتالوج (Catalog Layer)

#### جدول المصنعين (`manufacturers`)

```sql
CREATE TABLE manufacturers (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    website    TEXT,
    notes      TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### جدول أنواع القطع والأجهزة (`component_types`)

```sql
CREATE TABLE component_types (
    id           TEXT PRIMARY KEY,
    slug         TEXT NOT NULL UNIQUE,
    label_ar     TEXT NOT NULL,
    label_en     TEXT,
    icon         TEXT,
    is_builtin   INTEGER DEFAULT 0 CHECK (is_builtin IN (0, 1)),
    specs_schema TEXT DEFAULT '{}',
    created_at   TEXT DEFAULT (datetime('now'))
);
```

#### جدول كتالوج الموديلات (`asset_models`)

> قلب الكتالوج: كل موديل يُعرَّف مرة واحدة ويُشارك بين جميع الأصول الفيزيائية المتماثلة.

```sql
CREATE TABLE asset_models (
    id                TEXT PRIMARY KEY,
    manufacturer_id   TEXT REFERENCES manufacturers(id) ON DELETE SET NULL,
    component_type_id TEXT NOT NULL REFERENCES component_types(id),
    name              TEXT NOT NULL,       -- "Latitude E6440" / "980 PRO 1TB"
    model_number      TEXT,                -- SKU / MPN الدقيق من المصنع
    default_specs     TEXT DEFAULT '{}',   -- JSON مواصفات الموديل الافتراضية
    notes             TEXT,
    created_at        TEXT DEFAULT (datetime('now')),

    UNIQUE (manufacturer_id, model_number) -- منع تكرار نفس الموديل للمصنع نفسه
);
```

---

### 3.2 طبقة المخزون (Inventory Layer)

#### جدول الأشخاص (`persons`)

```sql
CREATE TABLE persons (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    phone        TEXT,
    relationship TEXT,  -- 'صديق' | 'زميل عمل' | 'عائلة' | 'عميل' | 'موظف'
    notes        TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);
```

#### جدول الأصول الموحد (`assets`) — قلب المخزون

> يمثل كل أصل فيزيائي تملكه: جهاز حاسوبي كامل، أو قطعة رام، أو هارد، أو كرت شاشة.
> القطعة المركبة داخل جهاز تحمل `parent_asset_id` يشير لذلك الجهاز.

```sql
CREATE TABLE assets (
    id                 TEXT PRIMARY KEY,
    asset_model_id     TEXT REFERENCES asset_models(id) ON DELETE SET NULL,
    parent_asset_id    TEXT REFERENCES assets(id) ON DELETE SET NULL,
    assigned_person_id TEXT REFERENCES persons(id) ON DELETE SET NULL,
    assigned_at        TEXT,
    name               TEXT,              -- اسم ودي مخصص (اختياري)
    serial_number      TEXT,
    slot_or_bus        TEXT,              -- المنفذ إن كانت القطعة مركبة (DIMM 1, M.2...)
    specs              TEXT DEFAULT '{}', -- JSON خاص بهذا الأصل (يتجاوز default_specs عند الحاجة)
    status             TEXT NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','in_storage','with_person','installed','faulty','sold')),
    storage_box_label  TEXT,
    notes              TEXT,
    first_seen_at      TEXT DEFAULT (datetime('now')),
    last_seen_at       TEXT DEFAULT (datetime('now')),
    created_at         TEXT DEFAULT (datetime('now')),
    updated_at         TEXT DEFAULT (datetime('now')),

    -- قيود سلامة البيانات
    CHECK (
        -- قطعة مركبة: لها جهاز أب ولا شخص
        (status = 'installed'   AND parent_asset_id IS NOT NULL AND assigned_person_id IS NULL)
        OR
        -- في التخزين: بدون جهاز وبدون شخص
        (status = 'in_storage'  AND parent_asset_id IS NULL     AND assigned_person_id IS NULL)
        OR
        -- مع شخص: بدون تركيب في جهاز
        (status = 'with_person' AND parent_asset_id IS NULL     AND assigned_person_id IS NOT NULL)
        OR
        -- حالات حرة: جهاز نشط أو تالف أو مباع
        (status IN ('active', 'faulty', 'sold'))
    )
);
```

#### جدول تفاصيل الأجهزة المجمعة (`device_profiles`)

> مرتبط 1-to-1 بجدول `assets`. يوجد فقط للأصول التي هي أجهزة حاسوبية مجمعة (لابتوب، مكتبي، سيرفر).

```sql
CREATE TABLE device_profiles (
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
```

#### جدول سجل العُهد (`custody_logs`)

> سجل تاريخي لا يُحذف. يتتبع كل حركة لكل أصل عبر الزمن.

```sql
CREATE TABLE custody_logs (
    id         TEXT PRIMARY KEY,
    asset_id   TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    person_id  TEXT REFERENCES persons(id) ON DELETE SET NULL,
    action     TEXT NOT NULL
                    CHECK (action IN ('assigned','returned','sold','stored','installed','uninstalled')),
    notes      TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

| قيمة `action` | المعنى |
|---------------|--------|
| `assigned` | تم تسليم الأصل لشخص |
| `returned` | تم استرداد الأصل من الشخص |
| `sold` | تم بيع الأصل |
| `stored` | تم وضعه في التخزين/الدرج |
| `installed` | تم تركيب القطعة داخل جهاز |
| `uninstalled` | تم فك القطعة من الجهاز |

#### جدول جلسات الفحص (`scan_sessions`)

```sql
CREATE TABLE scan_sessions (
    id         TEXT PRIMARY KEY,
    asset_id   TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    scanned_at TEXT DEFAULT (datetime('now')),
    source     TEXT DEFAULT 'CPU-Z',
    file_name  TEXT,
    raw_text   TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### جدول سجل التغييرات (`hardware_drift_logs`)

```sql
CREATE TABLE hardware_drift_logs (
    id               TEXT PRIMARY KEY,
    scan_session_id  TEXT REFERENCES scan_sessions(id) ON DELETE SET NULL,
    asset_id         TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    changed_asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
    change_type      TEXT NOT NULL
                          CHECK (change_type IN ('PART_ADDED','PART_REMOVED','PART_SWAPPED','SPECS_CHANGED')),
    identifier       TEXT,              -- السيريال أو المنفذ
    old_state        TEXT DEFAULT '{}',
    new_state        TEXT DEFAULT '{}',
    is_acknowledged  INTEGER DEFAULT 0 CHECK (is_acknowledged IN (0, 1)),
    detected_at      TEXT DEFAULT (datetime('now'))
);
```

---

## 4. Triggers

```sql
-- تحديث updated_at تلقائياً عند كل تعديل على assets
CREATE TRIGGER trg_assets_updated_at
AFTER UPDATE ON assets
FOR EACH ROW
WHEN OLD.updated_at = NEW.updated_at
BEGIN
    UPDATE assets SET updated_at = datetime('now') WHERE id = NEW.id;
END;
```

---

## 5. الفهارس (Indexes)

```sql
-- manufacturers
CREATE INDEX IF NOT EXISTS idx_manufacturers_name   ON manufacturers(name);

-- component_types
CREATE INDEX IF NOT EXISTS idx_comp_types_slug      ON component_types(slug);
CREATE INDEX IF NOT EXISTS idx_comp_types_builtin   ON component_types(is_builtin);

-- asset_models
CREATE INDEX IF NOT EXISTS idx_models_manufacturer  ON asset_models(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_models_type          ON asset_models(component_type_id);
CREATE INDEX IF NOT EXISTS idx_models_number        ON asset_models(model_number);

-- assets (الأهم)
CREATE INDEX IF NOT EXISTS idx_assets_model         ON assets(asset_model_id);
CREATE INDEX IF NOT EXISTS idx_assets_parent        ON assets(parent_asset_id);
CREATE INDEX IF NOT EXISTS idx_assets_person        ON assets(assigned_person_id);
CREATE INDEX IF NOT EXISTS idx_assets_serial        ON assets(serial_number);
CREATE INDEX IF NOT EXISTS idx_assets_status        ON assets(status);

-- custody_logs
CREATE INDEX IF NOT EXISTS idx_custody_asset        ON custody_logs(asset_id);
CREATE INDEX IF NOT EXISTS idx_custody_person       ON custody_logs(person_id);
CREATE INDEX IF NOT EXISTS idx_custody_action       ON custody_logs(action);
CREATE INDEX IF NOT EXISTS idx_custody_time         ON custody_logs(created_at);

-- scan_sessions & drift_logs
CREATE INDEX IF NOT EXISTS idx_scan_asset           ON scan_sessions(asset_id);
CREATE INDEX IF NOT EXISTS idx_drift_asset          ON hardware_drift_logs(asset_id);
CREATE INDEX IF NOT EXISTS idx_drift_changed        ON hardware_drift_logs(changed_asset_id);
CREATE INDEX IF NOT EXISTS idx_drift_ack            ON hardware_drift_logs(is_acknowledged);
```

---

## 6. البيانات الأولية (Seed Data)

```sql
-- أنواع مدمجة ثابتة (is_builtin = 1)
INSERT INTO component_types (id, slug, label_ar, label_en, icon, is_builtin, specs_schema) VALUES
    ('ct-device',  'DEVICE',  'جهاز حاسوبي', 'Device',  '🖥️', 1, '{}'),

    ('ct-ram',     'RAM',     'ذاكرة رام',   'RAM',     '🧠', 1,
     '{"capacity_mb":{"type":"integer","label":"السعة (MB)"},
       "type":{"type":"string","label":"النوع","enum":["DDR3","DDR4","DDR5"]},
       "speed_mhz":{"type":"integer","label":"التردد (MHz)"},
       "voltage":{"type":"number","label":"الفولتية (V)"},
       "timings":{"type":"string","label":"التواقيت"},
       "module_format":{"type":"string","label":"الشكل","enum":["SO-DIMM","UDIMM","RDIMM"]}}'),

    ('ct-storage', 'STORAGE', 'وحدة تخزين', 'Storage', '💾', 1,
     '{"capacity_gb":{"type":"number","label":"السعة (GB)"},
       "interface":{"type":"string","label":"الواجهة","enum":["SATA","NVMe","USB","PCIe"]},
       "form_factor":{"type":"string","label":"الشكل","enum":["2.5\"","3.5\"","M.2 2280","M.2 2242"]},
       "rpm":{"type":"integer","label":"السرعة (RPM)","nullable":true},
       "nand_type":{"type":"string","label":"نوع NAND","enum":["SLC","MLC","TLC","QLC"],"nullable":true}}'),

    ('ct-gpu',     'GPU',     'كرت شاشة',   'GPU',     '🎮', 1,
     '{"vram_mb":{"type":"integer","label":"حجم الذاكرة (MB)"},
       "vram_type":{"type":"string","label":"نوع الذاكرة","enum":["GDDR5","GDDR6","GDDR6X"]},
       "interface":{"type":"string","label":"الواجهة","enum":["PCIe x16","PCIe x8","Integrated"]},
       "tdp_watts":{"type":"integer","label":"الطاقة (W)"},
       "is_integrated":{"type":"boolean","label":"مدمج في المعالج"}}'),

    ('ct-cpu',     'CPU',     'معالج',       'CPU',     '⚙️', 1,
     '{"cores":{"type":"integer","label":"الأنوية"},
       "threads":{"type":"integer","label":"المسارات"},
       "base_ghz":{"type":"number","label":"التردد الأساسي (GHz)"},
       "boost_ghz":{"type":"number","label":"أقصى تردد (GHz)"},
       "socket":{"type":"string","label":"المقبس"},
       "tdp_watts":{"type":"integer","label":"الطاقة (W)"}}'),

    ('ct-battery', 'BATTERY', 'بطارية',      'Battery', '🔋', 1,
     '{"capacity_mwh":{"type":"integer","label":"السعة (mWh)"},
       "voltage_v":{"type":"number","label":"الجهد (V)"},
       "cells":{"type":"integer","label":"عدد الخلايا"},
       "chemistry":{"type":"string","label":"نوع الكيمياء","enum":["Li-Ion","Li-Po","NiMH"]}}'),

    ('ct-screen',  'SCREEN',  'شاشة',        'Screen',  '🖥', 1,
     '{"size_inch":{"type":"number","label":"المقاس (بوصة)"},
       "resolution":{"type":"string","label":"الدقة"},
       "panel_type":{"type":"string","label":"نوع اللوحة","enum":["IPS","TN","VA","OLED"]},
       "refresh_hz":{"type":"integer","label":"معدل التحديث (Hz)"}}'),

    ('ct-network', 'NETWORK', 'كرت شبكة',   'Network', '📡', 1,
     '{"interface":{"type":"string","label":"الواجهة","enum":["PCIe","USB","M.2","Integrated"]},
       "speed_gbps":{"type":"number","label":"السرعة (Gbps)"},
       "has_wifi":{"type":"boolean","label":"يدعم Wi-Fi"},
       "has_bluetooth":{"type":"boolean","label":"يدعم Bluetooth"}}'),

    ('ct-other',   'OTHER',   'قطعة أخرى',   'Other',   '🔧', 1, '{}');
```

---

## 7. الاستعلامات الرئيسية

### 7.1 ما بحوزة شخص معين؟
```sql
SELECT
    a.id,
    ct.label_ar                        AS النوع,
    COALESCE(a.name, am.name, '—')     AS الاسم,
    m.name                             AS المصنع,
    a.serial_number                    AS السيريال,
    a.assigned_at                      AS منذ
FROM assets a
LEFT JOIN asset_models am    ON a.asset_model_id    = am.id
LEFT JOIN manufacturers m    ON am.manufacturer_id  = m.id
LEFT JOIN component_types ct ON am.component_type_id = ct.id
WHERE a.assigned_person_id = :person_id
ORDER BY a.assigned_at DESC;
```

### 7.2 ما القطع المركبة داخل جهاز؟
```sql
SELECT
    a.id,
    ct.label_ar                        AS النوع,
    COALESCE(a.name, am.name, '—')     AS الاسم,
    m.name                             AS المصنع,
    a.serial_number                    AS السيريال,
    a.slot_or_bus                      AS المنفذ,
    a.specs                            AS المواصفات
FROM assets a
LEFT JOIN asset_models am    ON a.asset_model_id    = am.id
LEFT JOIN manufacturers m    ON am.manufacturer_id  = m.id
LEFT JOIN component_types ct ON am.component_type_id = ct.id
WHERE a.parent_asset_id = :device_asset_id
ORDER BY ct.slug, a.slot_or_bus;
```

### 7.3 تاريخ أصل كامل (عُهدة + حركات)
```sql
SELECT
    cl.created_at                      AS التاريخ,
    cl.action                          AS الحدث,
    COALESCE(p.name, '—')             AS الشخص,
    cl.notes                           AS الملاحظة
FROM custody_logs cl
LEFT JOIN persons p ON cl.person_id = p.id
WHERE cl.asset_id = :asset_id
ORDER BY cl.created_at DESC;
```

### 7.4 شجرة الجهاز الكاملة (Recursive CTE — SQLite 3.35+)
```sql
WITH RECURSIVE asset_tree AS (
    SELECT id, asset_model_id, parent_asset_id, serial_number, slot_or_bus, 0 AS depth
    FROM assets WHERE id = :root_device_id

    UNION ALL

    SELECT a.id, a.asset_model_id, a.parent_asset_id, a.serial_number, a.slot_or_bus, t.depth + 1
    FROM assets a
    JOIN asset_tree t ON a.parent_asset_id = t.id
)
SELECT
    at.depth,
    ct.label_ar                        AS النوع,
    COALESCE(am.name, '—')            AS الموديل,
    at.serial_number                   AS السيريال,
    at.slot_or_bus                     AS المنفذ
FROM asset_tree at
LEFT JOIN asset_models am    ON at.asset_model_id   = am.id
LEFT JOIN component_types ct ON am.component_type_id = ct.id
ORDER BY at.depth, ct.slug;
```

### 7.5 تسليم أصل لشخص (مع تسجيل السجل التاريخي)
```sql
-- الخطوة 1: تحديث حالة الأصل
UPDATE assets
SET assigned_person_id = :person_id,
    assigned_at        = datetime('now'),
    status             = 'with_person'
WHERE id = :asset_id;

-- الخطوة 2: تسجيل الحدث في السجل التاريخي
INSERT INTO custody_logs (id, asset_id, person_id, action, notes)
VALUES (:new_uuid, :asset_id, :person_id, 'assigned', :notes);
```

### 7.6 استرجاع أصل من شخص
```sql
-- الخطوة 1: تحديث حالة الأصل
UPDATE assets
SET assigned_person_id = NULL,
    assigned_at        = NULL,
    status             = 'in_storage'   -- أو 'active' للأجهزة
WHERE id = :asset_id;

-- الخطوة 2: تسجيل الاسترجاع
INSERT INTO custody_logs (id, asset_id, person_id, action, notes)
VALUES (:new_uuid, :asset_id, :person_id, 'returned', :notes);
```

---

## 8. سيناريو استيراد تقرير CPU-Z

```
1. تحليل الملف النصي
   ↓
2. مطابقة/إنشاء manufacturer: "Dell"
   ↓
3. مطابقة/إنشاء asset_model: "Latitude E6440" (نوع: DEVICE)
   ↓
4. مطابقة/إنشاء asset (الجهاز الرئيسي):
      - المطابقة بـ: system_serial أو system_uuid (من device_profiles)
      - إن لم يوجد: أنشئ asset جديد + device_profile
   ↓
5. تحديث device_profile: بيوس، لوحة، معالج، total_ram_mb، total_storage_gb
   ↓
6. لكل شريحة رام في قسم [Memory SPD]:
      a. مطابقة/إنشاء manufacturer: "Samsung"
      b. مطابقة/إنشاء asset_model: "8GB DDR4 3200MHz SO-DIMM"
      c. مطابقة/إنشاء asset (القطعة):
            - المطابقة بـ: serial_number + parent_asset_id
            - الحقل: slot_or_bus = "DIMM 1"
            - الحقل: status = 'installed'
   ↓
7. لكل هارد في قسم [Storage]:
      نفس منطق الخطوة 6
   ↓
8. مقارنة الحالة الجديدة بالسابقة → تسجيل hardware_drift_logs
   ↓
9. تسجيل scan_session (مع raw_text للأرشفة)
   ↓
10. تحديث last_seen_at لكل أصل تم تأكيده
```

---

## 9. ملخص الجداول

| الجدول | الطبقة | الغرض |
|--------|--------|--------|
| `manufacturers` | كتالوج | قائمة المصنعين |
| `component_types` | كتالوج | أنواع القطع والأجهزة |
| `asset_models` | كتالوج | موديلات المنتجات (مرجع مشترك) |
| `persons` | مخزون | الأشخاص المرتبطون بالعُهد |
| `assets` | مخزون | كل أصل فيزيائي تملكه |
| `device_profiles` | مخزون | تفاصيل الأجهزة المجمعة |
| `custody_logs` | تاريخ | سجل حركات العُهد |
| `scan_sessions` | تاريخ | جلسات استيراد CPU-Z |
| `hardware_drift_logs` | تاريخ | تغييرات العتاد المكتشفة |

---

## 10. مقارنة الإصدارات

| الميزة | v1.0 | v2.1 | **v3.0** |
|--------|------|------|----------|
| جدولان (devices + components) | ✅ | ✅ | ❌ دُمجا في `assets` |
| كتالوج الموديلات (`asset_models`) | ❌ | ❌ | ✅ |
| كتالوج المصنعين (`manufacturers`) | ❌ | ❌ | ✅ |
| منع تكرار الموديل (UNIQUE) | ❌ | ❌ | ✅ |
| FK حقيقي في `custody_logs` | ❌ Polymorphic | ❌ Polymorphic | ✅ `asset_id` مباشر |
| استعلام عهدة شخص | UNION ALL | UNION ALL | ✅ SELECT واحد |
| شجرة الأصول (Recursive CTE) | ❌ | ❌ | ✅ `parent_asset_id` |
| تفاصيل الجهاز المجمع | في `devices` | في `devices` | ✅ `device_profiles` |
| `component_types` | ❌ | ✅ | ✅ (محسّن) |
| CHECK constraints | ❌ | ✅ | ✅ (محسّنة) |
| Triggers لـ `updated_at` | ❌ | ✅ | ✅ |

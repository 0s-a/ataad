# 🖥️ عَتاد (Ataad) — Local Hardware Asset & Custody Management System

<div align="center">

![Ataad Banner](https://img.shields.io/badge/Ataad-v3.0.0-09090b?style=for-the-badge&logo=medusa&logoColor=white)
[![Python 3.13](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite WAL](https://img.shields.io/badge/SQLite-3.38+--WAL-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-zinc?style=for-the-badge)](LICENSE)

**نظام محلي، مستقل، وسريع جداً لإدارة الأصول العتادية، قطع الغيار، ومتابعة العُهد الشخصية والتاريخية**
*مستوحى من بساطة وفخامة نظام التصميم Medusa UI وبدعم كامل للغة العربية (RTL)*

</div>

---

## 📌 نبذة عن النظام (About Ataad)

**عَتاد** هو نظام ويب محلي موجه للتقنيين، مدراء الأنظمة، وهواة تجميع الحواسيب والمختبرات المنزلية (HomeLabs). يوفر حلاً متكاملاً لأرشفة ومتابعة الأجهزة الإلكترونية وقطع الغيار دون الحاجة إلى الاتصال بأي خوادم خارجية أو سحابية.

يعمل النظام محلياً بالكامل عبر قاعدة بيانات **SQLite 3** معمارية **WAL Mode**، ويتضمن محركاً ذكياً لتحليل تقارير أداة **CPU-Z** تلقائياً ومطابقتها مع قطع المخزون لاكتشاف أي تغييرات أو تعديلات عتادية (Hardware Drift Detection).

---

## ✨ المميزات الرئيسية (Key Features)

* **🏢 فصل الكتالوج عن المخزون (Catalog & Inventory Separation):**
  المصنعون والموديلات في طبقة مرجعية موحدة، والأصول المملوكة فعلياً في طبقة مستقلة لمنع تكرار البيانات.

* **🧩 جدول أصول هرمي موحد (Unified Asset Hierarchy):**
  الحواسيب وقطع الغيار كيانات من نفس النوع، حيث ترتبط القطع بالأجهزة الحاضنة عبر علاقة `parent_asset_id` وتنتقل بين الحالات (`installed` / `in_storage` / `with_person`).

* **⚡ محرك استيراد تقارير CPU-Z الفوري:**
  رفع ملف تقرير نصي من CPU-Z (`.txt`) ليقوم النظام بتحليله واستخراج المعالج، اللوحة الأم، الرامات وسيريالاتها، ووحدات التخزين، مع مقارنتها بالمكونات المسجلة ورصد أي قطع أضيفت أو نزعت.

* **🤝 إدارة عُهد متكاملة وسجل تاريخي غير قابل للتعديل (Custody Timeline):**
  إعارة أي جهاز أو قطعة لشخص مع توثيق وقت التسليم والاسترجاع تلقائياً في سجل `custody_logs` مع دعم التصفية والبحث.

* **🎨 واجهة مستخدم بهوية Medusa UI باللغة العربية:**
  تصميم نقي وهادئ بدرجات الرمادي والزنك، حدود دقيقة 1px، ألواح جانبية منزلقة (Slide-over Drawers) بدلاً من النوافذ المنبثقة، خط Monospace للسيريالات، وأداء لحظي.

* **🔒 خصوصية 100% واستقلالية تامة:**
  يعمل محلياً بالكامل دون أي اتصال بالإنترنت أو إرسال بيانات لأي طرف ثالث.

---

## 🏛️ المعمارية التقنية (Architecture)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       الواجهة الأمامية (Frontend SPA)                     │
│       React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons          │
│       (Medusa UI Style • RTL Native • Dark/Light Mode • Slide-over Drawer) │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ REST API (JSON)
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       الخادم المحلي (FastAPI Backend)                      │
│   Python 3.13 + FastAPI + Pydantic v2 + Regex CPU-Z Parser Engine          │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ Native Python Driver
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    قاعدة البيانات المحلية (Local SQLite DB)                 │
│         ataad.db (WAL Mode • PRAGMA foreign_keys = ON • Schema v3.0)      │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 التشغيل بنقرة واحدة (Quick Start)

### 🐧 على نظام Linux أو macOS:
```bash
git clone https://github.com/0s-a/ataad.git
cd ataad
./run.sh
```
*سيقوم السكريبت بفحص بيئة العمل، تجهيز البيئة الافتراضية، بناء الواجهة، تشغيل الخادم، وفتح المتصفح تلقائياً على `http://localhost:8000`.*

---

### 🪟 على نظام Windows:
انقر نقراً مزدوجاً على ملف **`run.bat`** أو قم بتشغيله من سطر الأوامر (CMD/PowerShell):
```cmd
run.bat
```

---

### 🐳 باستخدام Docker و Docker Compose:
```bash
docker compose up -d
```
ثم افتح متصفحك على: `http://localhost:8000`

---

## 🧪 زراعة البيانات التجريبية (Demo Seed Data)

لتجربة النظام فوراً مع بيانات واقعية كاملة (أجهزة حاسوبية، قطع غيار بالدرج، جهات اتصال، وسجلات عُهد تاريخية):

```bash
# تفعيل البيئة الافتراضية
source backend/venv/bin/activate   # أو على ويندوز: backend\venv\Scripts\activate

# تشغيل سكريبت البيانات التأسيسية
python backend/scripts/seed_demo_data.py
```

---

## 🔬 تشغيل الاختبارات المؤتمتة (Running Tests)

يتضمن المشروع حزمة اختبارات تغطي كافة الوظائف ومحلل تقارير CPU-Z وملف حقيقي:

```bash
pytest
```
*جميع الاختبارات (31/31) تمر بنسبة نجاح 100%.*

---

## 📂 هيكل المشروع (Project Structure)

```text
ataad/
├── backend/                  # خادم الباك إند (FastAPI)
│   ├── app/
│   │   ├── api/              # نقاط نهاية REST API
│   │   ├── core/             # إعدادات النظام وقاعدة البيانات
│   │   ├── parsers/          # محلل تقارير CPU-Z ومطابق العتاد
│   │   ├── schemas/          # نماذج Pydantic v2
│   │   └── services/         # منطق الأعمال والخدمات
│   ├── scripts/              # سكريبتات البيانات التأسيسية
│   └── tests/                # حزمة الاختبارات الشاملة
├── frontend/                 # واجهة المستخدم (React + Tailwind)
│   ├── src/
│   │   ├── api/              # عميل الربط مع الـ API
│   │   ├── components/       # مكونات Medusa UI (Drawer, Modal, Badges...)
│   │   ├── pages/            # شاشات النظام (الأجهزة، الدرج، العهدة، الكتالوج)
│   │   └── types/            # تعريفات TypeScript الموحدة
├── docs/                     # وثائق المخطط والتصميم
│   ├── database_schema.md    # توثيق مخطط قاعدة البيانات v3.0
│   ├── cpuz_parser_spec.md   # توثيق مواصفات محلل CPU-Z
│   └── ui_and_workflows_spec.md # توثيق شاشات وتجربة الاستخدام
├── run.sh                    # سكريبت التشغيل بنقرة واحدة (Linux/macOS)
├── run.bat                   # سكريبت التشغيل بنقرة واحدة (Windows)
├── Dockerfile                # حزمة البناء متعددة المراحل
├── docker-compose.yml        # إعدادات Docker Compose
├── schema.sql                # مخطط قاعدة البيانات SQLite 3
└── pytest.ini                # إعدادات تشغيل Pytest
```

---

## 📄 رخصة الاستخدام (License)

هذا المشروع مرخص تحت رخصة **MIT**. يمكنك استخدامه، تعديله، وتوزيعه بحرية.

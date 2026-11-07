#!/usr/bin/env bash
# ==============================================================================
#  عَتاد (Ataad) — نظام إدارة الأجهزة والعتاد والقطع المحلية
#  سكريبت التشغيل بنقرة واحدة لأنظمة Linux و macOS
# ==============================================================================

set -e

# ألوان الطباعة في الطرفية
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# تحديد مسار المشروع الرئيسي
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════════╗"
echo "  ║                  عَتاد — ATAAD HARDWARE INVENTORY                 ║"
echo "  ║             نظام إدارة الأجهزة وقطع الغيار والعهدة المحلية        ║"
echo "  ╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ------------------------------------------------------------------------------
# 1. التحقق من وجود Python 3
# ------------------------------------------------------------------------------
echo -e "${YELLOW}🔍 [1/5] فحص متطلبات بيئة Python 3...${NC}"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo -e "${RED}❌ خطأ: لم يتم العثور على Python 3 مثبت في النظام!${NC}"
    echo -e "   لتثبيته على توزيعات دبيان وأوبونتو: ${BOLD}sudo apt update && sudo apt install python3 python3-venv python3-pip${NC}"
    echo -e "   لتثبيته على فيدورا: ${BOLD}sudo dnf install python3 python3-pip${NC}"
    echo -e "   لتثبيته على آرتش: ${BOLD}sudo pacman -S python python-pip${NC}"
    exit 1
fi

PY_VER=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON_BIN -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON_BIN -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo -e "${RED}❌ خطأ: إصدار Python الحالي ($PY_VER) قديم. يتطلب عَتاد إصدار 3.10 أو أحدث.${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ تم التحقق من Python بنجاح: $($PYTHON_BIN --version)${NC}"

# ------------------------------------------------------------------------------
# 2. التحقق من وجود Node.js و npm
# ------------------------------------------------------------------------------
echo -e "${YELLOW}🔍 [2/5] فحص متطلبات Node.js و npm...${NC}"

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}❌ خطأ: لم يتم العثور على Node.js أو npm!${NC}"
    echo -e "   الواجهة الأمامية تتطلب Node.js 18+ لبناء الأصول وتحديثها."
    echo -e "   لتثبيته: قم بزيارة https://nodejs.org أو ثبته عبر مدير الحزم الخاص بك."
    exit 1
fi

echo -e "${GREEN}   ✓ تم التحقق من Node.js بنجاح: $(node -v) (npm: $(npm -v))${NC}"

# ------------------------------------------------------------------------------
# 3. إعداد البيئة الافتراضية للبايثون وتثبيت المكتبات
# ------------------------------------------------------------------------------
echo -e "${YELLOW}📦 [3/5] تجهيز البيئة الافتراضية وحزم الباك إند...${NC}"

VENV_DIR="$PROJECT_DIR/backend/venv"
REQS_FILE="$PROJECT_DIR/backend/requirements.txt"
STAMP_FILE="$VENV_DIR/.installed_requirements"

if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "   ⚙️ إنشاء بيئة افتراضية جديدة في backend/venv..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# تفعيل البيئة الافتراضية
source "$VENV_DIR/bin/activate"

# فحص وتثبيت requirements.txt عند الحاجة
NEEDS_INSTALL=0
if [ ! -f "$STAMP_FILE" ]; then
    NEEDS_INSTALL=1
elif [ "$REQS_FILE" -nt "$STAMP_FILE" ]; then
    NEEDS_INSTALL=1
fi

if [ "$NEEDS_INSTALL" -eq 1 ]; then
    echo -e "   📥 تثبيت مكتبات البايثون من requirements.txt..."
    pip install --upgrade pip --quiet
    pip install -r "$REQS_FILE" --quiet
    touch "$STAMP_FILE"
    echo -e "${GREEN}   ✓ تم تثبيت مكتبات الباك إند بنجاح.${NC}"
else
    echo -e "${GREEN}   ✓ بيئة البايثون ومكتباتها جاهزة ومحدثة.${NC}"
fi

# ------------------------------------------------------------------------------
# 4. فحص وبناء الواجهة الأمامية (Frontend SPA)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}🎨 [4/5] فحص واجهة المستخدم وبناء الملفات الثابتة...${NC}"

FRONTEND_DIST="$PROJECT_DIR/frontend/dist"
FRONTEND_DIR="$PROJECT_DIR/frontend"

REBUILD_FRONTEND=0
if [ ! -f "$FRONTEND_DIST/index.html" ]; then
    REBUILD_FRONTEND=1
elif [ "$1" == "--rebuild" ]; then
    REBUILD_FRONTEND=1
fi

if [ "$REBUILD_FRONTEND" -eq 1 ]; then
    echo -e "   🔨 بناء حزمة الواجهة الأمامية (dist)..."
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo -e "   📥 تثبيت مكتبات الواجهة الأمامية (npm install)..."
        (cd "$FRONTEND_DIR" && npm install --silent)
    fi
    (cd "$FRONTEND_DIR" && npm run build)
    echo -e "${GREEN}   ✓ تم بناء واجهة المستخدم بنجاح في frontend/dist.${NC}"
else
    echo -e "${GREEN}   ✓ واجهة المستخدم مبنية مسبقاً وجاهزة.${NC}"
fi

# ------------------------------------------------------------------------------
# 5. استخراج عناوين الشبكة وتشغيل الخادم
# ------------------------------------------------------------------------------
echo -e "${YELLOW}🚀 [5/5] إطلاق خادم عَتاد وفتح المتصفح...${NC}"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

# اكتشاف عنوان IP للشبكة المحلية (LAN) لعرضه
LAN_IP=""
if command -v hostname >/dev/null 2>&1; then
    LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
if [ -z "$LAN_IP" ]; then
    LAN_IP="127.0.0.1"
fi

# التحقق مما إذا كان المنفذ مستخدماً
if command -v ss >/dev/null 2>&1; then
    if ss -tuln | grep -q ":$PORT "; then
        echo -e "${YELLOW}⚠️  تنبيه: المنفذ $PORT يبدو قيد الاستخدام حالياً!${NC}"
        echo -e "   يمكنك تشغيل الخادم على منفذ آخر عبر تمرير المتغير PORT، مثال:"
        echo -e "   ${BOLD}PORT=8080 ./run.sh${NC}\n"
    fi
fi

# فتح المتصفح تلقائياً في الخلفية بعد بدء الخادم
(
    sleep 1.8
    URL="http://localhost:$PORT"
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$URL" >/dev/null 2>&1 || true
        elif command -v sensible-browser >/dev/null 2>&1; then
            sensible-browser "$URL" >/dev/null 2>&1 || true
        elif command -v open >/dev/null 2>&1; then
            open "$URL" >/dev/null 2>&1 || true
        else
            python3 -m webbrowser "$URL" >/dev/null 2>&1 || true
        fi
    fi
) &

echo -e "${GREEN}${BOLD}"
echo "  ✓ النظام يعمل بنجاح! الروابط المتاحة:"
echo "    ──────────────────────────────────────────────────────────"
echo "    💻 المتصفح المحلي:          http://localhost:$PORT"
echo "    📱 عبر الشبكة المنزلية/LAN:   http://$LAN_IP:$PORT"
echo "    📚 واجهات الـ API التفاعلية: http://localhost:$PORT/docs"
echo "    ──────────────────────────────────────────────────────────"
echo -e "${NC}"
echo -e "${CYAN}💡 للإيقاف: اضغط [Ctrl + C] في أي وقت.${NC}\n"

# تشغيل خادم Uvicorn
exec python3 -m uvicorn backend.app.main:app --host "$HOST" --port "$PORT"

@echo off
@chcp 65001 >nul
:: ==============================================================================
::  عَتاد (Ataad) — نظام إدارة الأجهزة والعتاد والقطع المحلية
::  سكريبت التشغيل بنقرة واحدة لنظام Microsoft Windows
:: ==============================================================================

title عَتاد — ATAAD HARDWARE INVENTORY (Windows)
color 0B

cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════════════════╗
echo  ║                  عَتاد — ATAAD HARDWARE INVENTORY                 ║
echo  ║             نظام إدارة الأجهزة وقطع الغيار والعهدة المحلية        ║
echo  ╚══════════════════════════════════════════════════════════════════╝
echo.

:: ------------------------------------------------------------------------------
:: 1. التحقق من وجود Python 3
:: ------------------------------------------------------------------------------
echo [1/5] فحص متطلبات بيئة Python 3...

set "PYTHON_EXE=python"
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    py -3 --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_EXE=py -3"
    ) else (
        color 0C
        echo.
        echo [خطأ فادح] لم يتم العثور على Python 3 مثبت في النظام!
        echo يرجى تحميل بايثون وتثبيته من الرابط: https://www.python.org/downloads/
        echo ** مهم جداً: تأكد من تفعيل خيار "Add python.exe to PATH" أثناء التثبيت **
        echo.
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%i in ('%PYTHON_EXE% --version') do set "PY_VER=%%i"
echo    [+] تم التحقق من Python بنجاح: %PY_VER%

:: ------------------------------------------------------------------------------
:: 2. التحقق من وجود Node.js و npm
:: ------------------------------------------------------------------------------
echo.
echo [2/5] فحص متطلبات Node.js و npm...

node -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo [خطأ فادح] لم يتم العثور على Node.js في النظام!
    echo الواجهة الأمامية تتطلب وجود Node.js لبناء الأصول وتجهيزها.
    echo يرجى تحميل وتثبيت الإصدار LTS من: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node -v') do set "NODE_VER=%%i"
for /f "tokens=*" %%i in ('npm -v') do set "NPM_VER=%%i"
echo    [+] تم التحقق من Node.js بنجاح: %NODE_VER% (npm: %NPM_VER%)

:: ------------------------------------------------------------------------------
:: 3. تجهيز البيئة الافتراضية وحزم الباك إند
:: ------------------------------------------------------------------------------
echo.
echo [3/5] تجهيز البيئة الافتراضية وحزم الباك إند...

if not exist "backend\venv\Scripts\activate.bat" (
    echo    [*] إنشاء البيئة الافتراضية في backend\venv...
    %PYTHON_EXE% -m venv backend\venv
    if %ERRORLEVEL% NEQ 0 (
        color 0C
        echo [خطأ] فشل إنشاء البيئة الافتراضية!
        pause
        exit /b 1
    )
)

call backend\venv\Scripts\activate.bat

if not exist "backend\venv\.installed_requirements" (
    echo    [*] تثبيت مكتبات البايثون من requirements.txt...
    python -m pip install --upgrade pip --quiet
    pip install -r backend\requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        color 0C
        echo [خطأ] حدث خطأ أثناء تثبيت مكتبات الباك إند!
        pause
        exit /b 1
    )
    type nul > backend\venv\.installed_requirements
    echo    [+] تم تثبيت مكتبات الباك إند بنجاح.
) else (
    echo    [+] بيئة البايثون ومكتباتها جاهزة ومحدثة.
)

:: ------------------------------------------------------------------------------
:: 4. فحص وبناء الواجهة الأمامية (Frontend SPA)
:: ------------------------------------------------------------------------------
echo.
echo [4/5] فحص واجهة المستخدم وبناء الملفات الثابتة...

if not exist "frontend\dist\index.html" (
    echo    [*] بناء حزمة الواجهة الأمامية لأول مرة...
    if not exist "frontend\node_modules" (
        echo    [*] تثبيت حزم واجهة المستخدم (npm install)...
        cd frontend
        call npm install --silent
        cd ..
    )
    cd frontend
    call npm run build
    cd ..
    echo    [+] تم بناء واجهة المستخدم بنجاح في frontend\dist.
) else (
    echo    [+] واجهة المستخدم مبنية مسبقاً وجاهزة.
)

:: ------------------------------------------------------------------------------
:: 5. إطلاق خادم عَتاد وفتح المتصفح
:: ------------------------------------------------------------------------------
echo.
echo [5/5] إطلاق خادم عَتاد وفتح المتصفح...

if "%PORT%"=="" set PORT=8000

echo.
echo   ==============================================================
echo     النظام يعمل بنجاح! الروابط المتاحة:
echo     ----------------------------------------------------------
echo     💻 المتصفح المحلي:          http://localhost:%PORT%
echo     📚 واجهات الـ API التفاعلية: http://localhost:%PORT/docs
echo   ==============================================================
echo   للإيقاف: اضغط [Ctrl + C] في نافذة الأوامر.
echo.

:: فتح المتصفح تلقائياً
start "" "http://localhost:%PORT%"

:: تشغيل خادم Uvicorn
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port %PORT%

pause

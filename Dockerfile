# ==============================================================================
#  عَتاد (Ataad v3.0) — Docker Multi-stage Production Build
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: بناء الواجهة الأمامية (Frontend Build)
# ------------------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: بيئة التشغيل النهائية (Production Runtime)
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ATAAD_DB_PATH=/app/data/ataad.db \
    ATAAD_SCHEMA_PATH=/app/schema.sql \
    ATAAD_FRONTEND_DIST=/app/frontend/dist \
    PORT=8000

WORKDIR /app

# تثبيت أدوات النظام الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# تثبيت متطلبات البايثون
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# نسخ مخطط قاعدة البيانات وملفات النظام
COPY schema.sql ./
COPY backend/ ./backend/

# نسخ مخرجات الواجهة الأمامية المبنية من المرحلة الأولى
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# تجهيز مجلد البيانات المحلية للمحافظة على استمرارية قاعدة البيانات
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

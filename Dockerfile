# Dockerfile مبسط لتجنب مشاكل الصلاحيات
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# تعيين مجلد العمل
WORKDIR /app

# تثبيت المتطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات أولاً للاستفادة من Docker cache
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p logs sessions archive exports backups config src utils

# تعريف المنفذ (اختياري للبوت)
EXPOSE 8080

# فحص صحة التطبيق
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('archive.db'); conn.close()" || exit 1

# أمر التشغيل المباشر
CMD ["python", "run.py"]

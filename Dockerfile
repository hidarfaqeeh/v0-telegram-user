# Dockerfile محسن مع إصلاح مشاكل الصلاحيات
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# تثبيت المتطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم غير جذر
RUN groupadd -r botuser && useradd -r -g botuser -d /app -s /bin/bash botuser

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ سكريبت البداية وإعطاؤه الصلاحيات
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# نسخ ملفات المشروع
COPY . .

# إنشاء المجلدات المطلوبة وإعطاء الصلاحيات
RUN mkdir -p logs sessions archive exports backups config src utils && \
    chown -R botuser:botuser /app

# التبديل للمستخدم غير الجذر
USER botuser

# تعريف المنفذ
EXPOSE 8080

# فحص صحة التطبيق
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('archive.db'); conn.close(); print('OK')" || exit 1

# أمر التشغيل
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "main.py"]

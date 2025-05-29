# استخدام Python 3.11 كصورة أساسية
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

# إنشاء مستخدم غير جذر للأمان
RUN groupadd -r botuser && useradd -r -g botuser botuser

# نسخ ملف المتطلبات أولاً للاستفادة من Docker cache
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p logs sessions archive exports backups config src utils

# تغيير ملكية الملفات للمستخدم الجديد
RUN chown -R botuser:botuser /app

# التبديل للمستخدم غير الجذر
USER botuser

# تعريف المنفذ (اختياري للبوت)
EXPOSE 8080

# فحص صحة التطبيق المحدث
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app'); from utils.diagnostics import check_database; print('OK' if check_database()['success'] else 'FAIL')" || exit 1

# نسخ سكريبت البداية
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# أمر التشغيل
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "run.py"]

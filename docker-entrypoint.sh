#!/bin/bash

# Telegram Archive Bot Startup Script - مُحدث لحل مشاكل asyncio

echo "🚀 Starting Telegram Archive Bot..."

# التحقق من متغيرات البيئة المطلوبة
required_vars=("API_ID" "API_HASH" "BOT_TOKEN")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var environment variable is not set"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# إنشاء المجلدات المطلوبة
mkdir -p logs sessions archive exports backups config

echo "✅ Directories created"

# تثبيت nest-asyncio إذا لم يكن مثبت
python -c "import nest_asyncio" 2>/dev/null || pip install nest-asyncio

echo "✅ Dependencies checked"

# التحقق من قاعدة البيانات
python -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('archive.db')
    conn.close()
    print('✅ Database connection test passed')
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
"

echo "✅ Database check completed"

# بدء التطبيق مع معالجة أفضل للأخطاء
echo "🤖 Starting bot application..."

# استخدام الملف المُصلح
if [ -f "main_fixed.py" ]; then
    exec python main_fixed.py
else
    exec python run.py
fi

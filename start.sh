#!/bin/bash

# Telegram Archive Bot Startup Script
# هذا السكريبت يتم تشغيله عند بدء الحاوية

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

# بدء التطبيق
echo "🤖 Starting bot application..."
exec python main.py

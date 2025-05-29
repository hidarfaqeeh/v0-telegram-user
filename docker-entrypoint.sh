#!/bin/bash
set -e

echo "🐳 بدء تشغيل بوت أرشفة تليغرام"

# التحقق من متغيرات البيئة المطلوبة
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "your_bot_token_here" ]; then
    echo "❌ BOT_TOKEN غير محدد أو يحتوي على قيمة افتراضية"
    echo "💡 يرجى تعديل متغيرات البيئة"
    exit 1
fi

if [ -z "$ADMIN_IDS" ] || [ "$ADMIN_IDS" = "123456789,987654321" ]; then
    echo "❌ ADMIN_IDS غير محدد أو يحتوي على قيمة افتراضية"
    echo "💡 يرجى تعديل متغيرات البيئة"
    exit 1
fi

echo "✅ متغيرات البيئة الأساسية محددة"

# إنشاء المجلدات المطلوبة
mkdir -p logs sessions archive exports backups config

echo "✅ المجلدات جاهزة"

# تشغيل الأمر المرسل
echo "🚀 بدء تشغيل البوت..."
exec "$@"

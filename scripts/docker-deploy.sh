#!/bin/bash

# سكريبت نشر Docker للبوت

set -e

echo "🚀 نشر بوت أرشفة تليغرام"
echo "=" * 40

# التحقق من ملف .env
if [ ! -f .env ]; then
    echo "❌ ملف .env غير موجود!"
    echo "💡 انسخ .env.example إلى .env وعدل القيم"
    exit 1
fi

echo "✅ ملف .env موجود"

# التحقق من متغيرات البيئة المطلوبة
source .env

required_vars=("API_ID" "API_HASH" "BOT_TOKEN" "ADMIN_IDS")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ متغيرات البيئة المفقودة:"
    printf '  - %s\n' "${missing_vars[@]}"
    echo "💡 يرجى تعديل ملف .env"
    exit 1
fi

echo "✅ متغيرات البيئة صحيحة"

# إنشاء مجلدات البيانات
echo "📁 إنشاء مجلدات البيانات..."
mkdir -p data/{archive,sessions,logs,exports,backups,config}

# بناء ونشر البوت
echo "🔨 بناء ونشر البوت..."
docker-compose down
docker-compose build
docker-compose up -d

echo "⏳ انتظار بدء تشغيل البوت..."
sleep 10

# التحقق من حالة البوت
if docker-compose ps | grep -q "Up"; then
    echo "✅ البوت يعمل بنجاح!"
    echo ""
    echo "📊 حالة الخدمات:"
    docker-compose ps
    echo ""
    echo "🔍 لمراقبة السجلات:"
    echo "docker-compose logs -f telegram-bot"
    echo ""
    echo "⏹️ لإيقاف البوت:"
    echo "docker-compose down"
else
    echo "❌ فشل في تشغيل البوت!"
    echo "🔍 فحص السجلات:"
    docker-compose logs telegram-bot
    exit 1
fi

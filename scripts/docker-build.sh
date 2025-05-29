#!/bin/bash

# سكريبت بناء Docker للبوت

set -e

echo "🐳 بناء صورة Docker لبوت أرشفة تليغرام"
echo "=" * 50

# متغيرات
IMAGE_NAME="telegram-archive-bot"
VERSION=${1:-"latest"}
BUILD_TYPE=${2:-"production"}

echo "📦 اسم الصورة: $IMAGE_NAME:$VERSION"
echo "🔧 نوع البناء: $BUILD_TYPE"

# إنشاء مجلدات البيانات
echo "📁 إنشاء مجلدات البيانات..."
mkdir -p data/{archive,sessions,logs,exports,backups,config}

# بناء الصورة
if [ "$BUILD_TYPE" = "development" ]; then
    echo "🔨 بناء صورة التطوير..."
    docker build -f Dockerfile.dev -t $IMAGE_NAME:$VERSION-dev .
    echo "✅ تم بناء صورة التطوير: $IMAGE_NAME:$VERSION-dev"
else
    echo "🔨 بناء صورة الإنتاج..."
    docker build -t $IMAGE_NAME:$VERSION .
    echo "✅ تم بناء صورة الإنتاج: $IMAGE_NAME:$VERSION"
fi

# عرض معلومات الصورة
echo "📊 معلومات الصورة:"
docker images $IMAGE_NAME:$VERSION

echo "🎉 تم بناء الصورة بنجاح!"
echo ""
echo "🚀 لتشغيل البوت:"
echo "docker-compose up -d"
echo ""
echo "🔍 لمراقبة السجلات:"
echo "docker-compose logs -f telegram-bot"

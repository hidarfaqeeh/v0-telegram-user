#!/bin/bash
set -e

echo "🐳 بدء تشغيل بوت أرشفة تليغرام في Docker"
echo "=" * 50

# التحقق من متغيرات البيئة المطلوبة
required_vars=("API_ID" "API_HASH" "BOT_TOKEN")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var environment variable is not set"
        echo "💡 Please set all required environment variables"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# إنشاء المجلدات المطلوبة
mkdir -p logs sessions archive exports backups config

echo "✅ Directories created"

# التحقق من الإعدادات
echo "🔧 Running setup check..."
python -c "
import sys
sys.path.append('/app')
from utils.setup import check_requirements
try:
    check_requirements()
    print('✅ Requirements check passed')
except Exception as e:
    print(f'❌ Requirements check failed: {e}')
    sys.exit(1)
"

# تشغيل تشخيص سريع
echo "🔍 Running quick diagnostics..."
python -c "
import sys, asyncio
sys.path.append('/app')
from config import Config
from utils.diagnostics import run_quick_diagnostics

async def quick_check():
    try:
        config = Config()
        results = await run_quick_diagnostics(config)
        if results['errors']:
            print('⚠️ Some issues found, but continuing...')
            for error in results['errors']:
                print(f'  - {error}')
        else:
            print('✅ Quick diagnostics passed')
    except Exception as e:
        print(f'⚠️ Diagnostics failed: {e}')

asyncio.run(quick_check())
"

echo "🚀 Starting bot application..."

# تشغيل الأمر المرسل
exec "$@"

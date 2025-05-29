# 🐳 دليل Docker لبوت أرشفة تليغرام

## 🚀 التشغيل السريع

### 1️⃣ إعداد متغيرات البيئة:
\`\`\`bash
cp .env.docker.example .env
# عدل ملف .env وأضف القيم الصحيحة
\`\`\`

### 2️⃣ بناء ونشر البوت:
\`\`\`bash
# استخدام السكريبت التلقائي
chmod +x scripts/docker-deploy.sh
./scripts/docker-deploy.sh

# أو يدوياً
docker-compose up -d
\`\`\`

### 3️⃣ مراقبة البوت:
\`\`\`bash
# مراقبة السجلات
docker-compose logs -f telegram-bot

# فحص حالة البوت
docker-compose ps

# دخول حاوية البوت
docker-compose exec telegram-bot bash
\`\`\`

## 🔧 أوامر Docker المفيدة

### إدارة الحاويات:
\`\`\`bash
# تشغيل البوت
docker-compose up -d

# إيقاف البوت
docker-compose down

# إعادة تشغيل البوت
docker-compose restart

# إعادة بناء البوت
docker-compose build --no-cache
\`\`\`

### مراقبة وتشخيص:
\`\`\`bash
# مراقبة السجلات المباشرة
docker-compose logs -f

# فحص استخدام الموارد
docker stats

# تشغيل تشخيص داخل الحاوية
docker-compose exec telegram-bot python run.py --diagnostics
\`\`\`

### إدارة البيانات:
\`\`\`bash
# نسخ احتياطي للبيانات
docker-compose exec telegram-bot tar -czf /tmp/backup.tar.gz archive/ sessions/ *.db
docker cp telegram-archive-bot-v2:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz

# استعادة البيانات
docker cp ./backup.tar.gz telegram-archive-bot-v2:/tmp/
docker-compose exec telegram-bot tar -xzf /tmp/backup.tar.gz
\`\`\`

## 🛠️ التطوير مع Docker

### تشغيل بيئة التطوير:
\`\`\`bash
# بناء صورة التطوير
docker build -f Dockerfile.dev -t telegram-archive-bot:dev .

# تشغيل بيئة التطوير
docker-compose -f docker-compose.dev.yml up -d

# دخول حاوية التطوير
docker-compose -f docker-compose.dev.yml exec telegram-bot-dev bash
\`\`\`

### اختبار التغييرات:
\`\`\`bash
# تشغيل الاختبارات
docker-compose exec telegram-bot python -m pytest

# تشغيل اختبار بسيط
docker-compose exec telegram-bot python run.py --test
\`\`\`

## 📊 المراقبة والصحة

### فحص صحة البوت:
\`\`\`bash
# فحص صحة الحاوية
docker-compose exec telegram-bot python -c "
import sys
sys.path.append('/app')
from utils.diagnostics import check_database
result = check_database()
print('✅ صحي' if result['success'] else '❌ مشكلة')
"
\`\`\`

### مراقبة الموارد:
\`\`\`bash
# مراقبة استخدام الذاكرة والمعالج
docker stats telegram-archive-bot-v2

# فحص مساحة القرص
docker-compose exec telegram-bot df -h
\`\`\`

## 🔒 الأمان

### أفضل الممارسات:
- ✅ استخدام مستخدم غير جذر في الحاوية
- ✅ تشفير متغيرات البيئة الحساسة
- ✅ تحديث الصورة الأساسية بانتظام
- ✅ مراقبة السجلات للأنشطة المشبوهة

### تحديث الأمان:
\`\`\`bash
# تحديث الصورة الأساسية
docker pull python:3.11-slim

# إعادة بناء مع آخر التحديثات
docker-compose build --no-cache --pull
\`\`\`

## 🚨 استكشاف الأخطاء

### مشاكل شائعة:

#### البوت لا يبدأ:
\`\`\`bash
# فحص السجلات
docker-compose logs telegram-bot

# فحص متغيرات البيئة
docker-compose exec telegram-bot env | grep -E "(API_|BOT_|ADMIN_)"
\`\`\`

#### مشاكل الذاكرة:
\`\`\`bash
# زيادة حد الذاكرة في docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G  # زيادة من 512M
\`\`\`

#### مشاكل الشبكة:
\`\`\`bash
# فحص الاتصال بالإنترنت
docker-compose exec telegram-bot ping -c 3 api.telegram.org

# فحص DNS
docker-compose exec telegram-bot nslookup api.telegram.org
\`\`\`

## 📦 النشر في الإنتاج

### إعدادات الإنتاج:
\`\`\`yaml
# في docker-compose.yml
environment:
  - ENVIRONMENT=production
  - DEBUG=false
  
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
  restart_policy:
    condition: unless-stopped
\`\`\`

### مراقبة الإنتاج:
\`\`\`bash
# تفعيل المراقبة
docker-compose --profile monitoring up -d

# الوصول لمقاييس الأداء
curl http://localhost:9100/metrics
\`\`\`

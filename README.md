# 🤖 Telegram Archive Bot

[![Deploy to Northflank](https://img.shields.io/badge/Deploy-Northflank-blue)](https://northflank.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-green)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)

بوت تليغرام متقدم لأرشفة القنوات بطريقة منظمة وتلقائية مع نشر سحابي على Northflank.

## ✨ المميزات

- 🔄 **أرشفة تلقائية** للرسائل الجديدة
- 📅 **أرشفة يدوية** بتواريخ مخصصة  
- 🗂️ **تنظيم هرمي** (سنة/شهر/يوم)
- 🔍 **بحث متقدم** في المحتوى
- 📤 **تصدير واستيراد** البيانات
- 🎛️ **لوحة تحكم تفاعلية**
- 🐳 **جاهز للـ Docker**
- ☁️ **نشر تلقائي** على Northflank

## 🚀 النشر السريع

### على Northflank (موصى به):

1. **Fork هذا المستودع**
2. **إعداد Northflank:**
   - إنشاء مشروع جديد
   - ربط GitHub repository
   - إضافة متغيرات البيئة
3. **النشر التلقائي:** كل push سيؤدي لنشر تلقائي

### محلياً مع Docker:

\`\`\`bash
# استنساخ المستودع
git clone https://github.com/YOUR_USERNAME/telegram-archive-bot.git
cd telegram-archive-bot

# إعداد متغيرات البيئة
cp .env.example .env
# عدل القيم في .env

# تشغيل مع Docker
docker-compose up -d
\`\`\`

## ⚙️ متغيرات البيئة المطلوبة

\`\`\`env
API_ID=your_api_id                    # من my.telegram.org
API_HASH=your_api_hash                # من my.telegram.org  
BOT_TOKEN=your_bot_token              # من @BotFather
PHONE_NUMBER=+1234567890              # رقم هاتفك
SOURCE_CHANNEL=@your_channel          # القناة للأرشفة
ADMIN_IDS=123456789,987654321         # معرفات المدراء
\`\`\`

## 📋 الأوامر

| الأمر | الوظيفة |
|-------|---------|
| `/start` | القائمة الرئيسية |
| `/status` | عرض الإحصائيات |
| `/browse` | تصفح الأرشيف |
| `/search كلمة` | البحث في المحتوى |
| `/archive_today` | أرشفة اليوم |
| `/archive_day YYYY-MM-DD` | أرشفة يوم محدد |
| `/export YYYY-MM-DD` | تصدير أرشيف |
| `/set_channel @channel` | تحديد القناة |

## 🔧 التطوير المحلي

\`\`\`bash
# إعداد البيئة
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate   # Windows

# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل البوت
python main.py
\`\`\`

## 📊 المراقبة والصحة

- **Health Checks:** فحص دوري لقاعدة البيانات
- **Logging:** سجلات مفصلة لجميع العمليات  
- **Metrics:** مراقبة الأداء والموارد
- **Auto-restart:** إعادة تشغيل تلقائي عند الأخطاء

## 🛡️ الأمان

- ✅ متغيرات البيئة آمنة
- ✅ مستخدم غير جذر في Docker
- ✅ تشفير البيانات الحساسة
- ✅ فحص صحة دوري

## 💰 التكلفة

### Northflank (تقديرية):
- **الموارد الأساسية:** ~$30/شهر
- **التخزين:** ~$5/شهر إضافي لكل 10GB
- **النقل:** مجاني حتى 100GB/شهر

## 📞 الدعم

- 🐛 **Issues:** GitHub Issues
- 💬 **Discussions:** GitHub Discussions
- 📧 **Email:** support@example.com

---

⭐ **إذا أعجبك المشروع، لا تنس إعطاؤه نجمة!**

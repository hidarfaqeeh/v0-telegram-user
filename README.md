# 🤖 بوت أرشفة تليغرام - الإصدار 2.0

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

بوت تليغرام متقدم لأرشفة القنوات بطريقة منظمة وتلقائية مع أدوات تشخيص مدمجة.

## ✨ المميزات الجديدة

- 🔧 **نظام إعداد تلقائي** للبيئة والمتطلبات
- 🔍 **أدوات تشخيص متقدمة** لحل المشاكل
- 🔐 **مدير String Session** مدمج
- 🧪 **اختبارات بسيطة** للتحقق من عمل البوت
- 📊 **نظام سجلات محسن** مع تواريخ
- ⚙️ **هيكل مشروع منظم** وقابل للصيانة

## 🚀 التثبيت والإعداد

### 1️⃣ الإعداد السريع:
\`\`\`bash
# استنساخ المشروع
git clone <repository-url>
cd telegram-archive-bot

# إعداد البيئة تلقائياً
python run.py --setup
\`\`\`

### 2️⃣ إنشاء String Session:
\`\`\`bash
python run.py --session
\`\`\`

### 3️⃣ اختبار البوت:
\`\`\`bash
python run.py --test
\`\`\`

### 4️⃣ تشغيل البوت:
\`\`\`bash
python run.py
\`\`\`

## 🔧 الأوامر المتاحة

### أوامر الإعداد:
\`\`\`bash
python run.py --setup        # إعداد البيئة والمتطلبات
python run.py --session      # إنشاء String Session
python run.py --diagnostics  # تشخيص شامل للمشاكل
python run.py --test         # اختبار بسيط للبوت
python run.py --debug        # تشغيل في وضع التصحيح
\`\`\`

### أوامر البوت في تليغرام:
- `/start` - القائمة الرئيسية التفاعلية
- `/status` - إحصائيات الأرشيف
- `/browse` - تصفح الأرشيف بالتواريخ
- `/search كلمة` - البحث في المحتوى
- `/archive_today` - أرشفة منشورات اليوم
- `/archive_day YYYY-MM-DD` - أرشفة يوم محدد
- `/export YYYY-MM-DD` - تصدير أرشيف كملف JSON
- `/set_channel @channel` - تحديد القناة المصدر
- `/diagnostics` - تشخيص سريع للبوت

## 📁 هيكل المشروع

\`\`\`
telegram-archive-bot/
├── run.py                 # نقطة البداية الرئيسية
├── config.py             # إعدادات البوت
├── src/
│   ├── __init__.py
│   └── bot.py           # الفئة الرئيسية للبوت
├── utils/
│   ├── __init__.py
│   ├── logger.py        # نظام السجلات
│   ├── setup.py         # أدوات الإعداد
│   ├── diagnostics.py  # أدوات التشخيص
│   ├── session_manager.py # مدير الجلسات
│   └── simple_test.py   # اختبارات بسيطة
├── archive/             # ملفات الأرشيف
├── exports/             # ملفات التصدير
├── logs/               # ملفات السجلات
├── sessions/           # ملفات الجلسات
└── .env               # متغيرات البيئة
\`\`\`

## ⚙️ متغيرات البيئة

\`\`\`env
# إعدادات Telethon (Userbot)
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890
STRING_SESSION=your_string_session_here

# إعدادات Bot Token
BOT_TOKEN=your_bot_token_here

# إعدادات القناة والمدراء
SOURCE_CHANNEL=@your_channel_username
ADMIN_IDS=123456789,987654321

# إعدادات إضافية
DEBUG=false
ENVIRONMENT=development
\`\`\`

## 🔍 استكشاف الأخطاء

### مشكلة شائعة: البوت لا يستجيب
\`\`\`bash
# تشغيل التشخيص الشامل
python run.py --diagnostics

# اختبار البوت البسيط
python run.py --test

# فحص السجلات
cat logs/bot_*.log
\`\`\`

### مشكلة: خطأ في String Session
\`\`\`bash
# إنشاء String Session جديد
python run.py --session
\`\`\`

### مشكلة: متطلبات مفقودة
\`\`\`bash
# إعادة إعداد البيئة
python run.py --setup
\`\`\`

## 📊 المراقبة والسجلات

- **السجلات اليومية**: `logs/bot_YYYYMMDD.log`
- **تقارير التشخيص**: `logs/diagnosis_*.json`
- **ملفات الجلسات**: `sessions/`

## 🛡️ الأمان

- ✅ متغيرات البيئة آمنة في `.env`
- ✅ String Session مشفر
- ✅ فحص صلاحيات المدراء
- ✅ سجلات مفصلة للعمليات

## 🤝 المساهمة

1. Fork المشروع
2. إنشاء فرع للميزة الجديدة
3. Commit التغييرات
4. Push للفرع
5. إنشاء Pull Request

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 📞 الدعم

- 🐛 **Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions
- 📧 **Email**: support@example.com

---

⭐ **إذا أعجبك المشروع، لا تنس إعطاؤه نجمة!**
\`\`\`

\`\`\`plaintext file="requirements.txt"
# مكتبات بوت أرشفة تليغرام - الإصدار 2.0
telethon>=1.28.5
python-telegram-bot>=20.0
python-dotenv>=1.0.0
aiofiles>=23.0.0
requests>=2.25.0

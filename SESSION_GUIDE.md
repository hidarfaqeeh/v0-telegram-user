# 📱 دليل إنشاء String Session

## 🎯 ما هو String Session؟

String Session هو نص مشفر يحتوي على معلومات جلسة Telegram الخاصة بك. يسمح للبوت بالاتصال بـ Telegram باستخدام حسابك دون الحاجة لإدخال رقم الهاتف في كل مرة.

## 🔧 الخطوات المطلوبة

### 1️⃣ الحصول على API Credentials

1. اذهب إلى: https://my.telegram.org/apps
2. سجل دخولك برقم هاتفك
3. اضغط على "Create new application"
4. املأ البيانات المطلوبة:
   - **App title:** Telegram Archive Bot
   - **Short name:** archive_bot
   - **Platform:** Desktop
5. انسخ **API_ID** و **API_HASH**

### 2️⃣ إنشاء String Session

\`\`\`bash
# تشغيل سكريبت إنشاء String Session
python create_session.py
\`\`\`

### 3️⃣ اتباع التعليمات

1. أدخل **API_ID** و **API_HASH**
2. أدخل رقم هاتفك بالتنسيق الدولي (مثل: +1234567890)
3. أدخل كود التحقق المرسل إليك
4. أدخل كلمة المرور إذا كانت مفعلة (Two-Factor Authentication)

### 4️⃣ نسخ String Session

بعد نجاح العملية، ستحصل على String Session مثل:
\`\`\`
1BVtsOHoBu6b4X8gK7X5F_lv4X8gK7X5F_lv4X8gK7X5F_lv4X8gK7X5F_lv4X8gK7X5F_lv...
\`\`\`

### 5️⃣ إضافة إلى ملف .env

\`\`\`env
# إعدادات Telethon
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
PHONE_NUMBER=+1234567890
STRING_SESSION=1BVtsOHoBu6b4X8gK7X5F_lv4X8gK7X5F_lv...

# باقي الإعدادات
BOT_TOKEN=your_bot_token_here
SOURCE_CHANNEL=@your_channel
ADMIN_IDS=123456789,987654321
\`\`\`

## ⚠️ تحذيرات مهمة

### 🔐 الأمان
- **لا تشارك String Session مع أحد**
- **لا ترفعه على GitHub أو أي مكان عام**
- **احتفظ به في مكان آمن**

### 🚫 المخاطر
- String Session يعطي وصول كامل لحسابك
- يمكن استخدامه لقراءة وإرسال الرسائل
- يمكن استخدامه للوصول لجميع المحادثات

### 🛡️ الحماية
- استخدم String Session فقط مع البوتات الموثوقة
- راجع الكود قبل الاستخدام
- فعّل Two-Factor Authentication على حسابك

## 🔄 إعادة إنشاء String Session

إذا تم اختراق String Session أو تريد إنشاء واحد جديد:

1. شغل `python create_session.py` مرة أخرى
2. أدخل نفس البيانات
3. استبدل String Session القديم بالجديد
4. String Session القديم سيصبح غير صالح تلقائياً

## 🆘 حل المشاكل الشائعة

### خطأ "Invalid session"
- تأكد من نسخ String Session كاملاً
- تأكد من عدم وجود مسافات إضافية
- جرب إنشاء String Session جديد

### خطأ "API_ID invalid"
- تأكد من صحة API_ID (يجب أن يكون رقماً)
- تأكد من نسخه من my.telegram.org بشكل صحيح

### خطأ "API_HASH invalid"
- تأكد من صحة API_HASH (32 حرف)
- تأكد من نسخه كاملاً دون مسافات

### خطأ "Phone number invalid"
- استخدم التنسيق الدولي (+1234567890)
- تأكد من صحة رقم الهاتف
- تأكد من أن الرقم مسجل في Telegram

## 💡 نصائح

1. **احتفظ بنسخة احتياطية** من String Session
2. **استخدم حساب منفصل** للبوت إذا أمكن
3. **راجع سجلات البوت** بانتظام
4. **فعّل التنبيهات الأمنية** في Telegram
5. **استخدم VPS آمن** للتشغيل

## 📞 الدعم

إذا واجهت مشاكل:
1. تأكد من اتباع الخطوات بالترتيب
2. راجع ملف السجل `logs/bot.log`
3. جرب إنشاء String Session جديد
4. تأكد من إعدادات الشبكة والـ VPN

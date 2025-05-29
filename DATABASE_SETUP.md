# 🗄️ دليل إعداد قاعدة البيانات

## 📋 أنواع قواعد البيانات المدعومة

### 1️⃣ SQLite (افتراضي)
\`\`\`env
DATABASE_URL=sqlite:///archive.db
\`\`\`
**المميزات:**
- ✅ لا يحتاج إعداد
- ✅ ملف واحد محلي
- ✅ سريع للمشاريع الصغيرة

### 2️⃣ PostgreSQL
\`\`\`env
DATABASE_URL=postgresql://username:password@localhost:5432/telegram_archive
\`\`\`
**المميزات:**
- ✅ قوي ومتقدم
- ✅ دعم البحث النصي المتقدم
- ✅ مناسب للمشاريع الكبيرة

### 3️⃣ MySQL
\`\`\`env
DATABASE_URL=mysql://username:password@localhost:3306/telegram_archive
\`\`\`
**المميزات:**
- ✅ شائع ومدعوم
- ✅ أداء جيد
- ✅ سهل الإدارة

## 🚀 إعداد قواعد البيانات الخارجية

### PostgreSQL على Ubuntu/Debian:
\`\`\`bash
# تثبيت PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# إنشاء قاعدة بيانات
sudo -u postgres createdb telegram_archive

# إنشاء مستخدم
sudo -u postgres createuser --interactive telegram_user

# تعيين كلمة مرور
sudo -u postgres psql
ALTER USER telegram_user PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE telegram_archive TO telegram_user;
\q
\`\`\`

### MySQL على Ubuntu/Debian:
\`\`\`bash
# تثبيت MySQL
sudo apt update
sudo apt install mysql-server

# إعداد MySQL
sudo mysql_secure_installation

# إنشاء قاعدة بيانات
sudo mysql
CREATE DATABASE telegram_archive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'telegram_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON telegram_archive.* TO 'telegram_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
\`\`\`

## 🔧 إعداد متغيرات البيئة

### ملف .env:
\`\`\`env
# اختر واحد من التالي:

# SQLite (محلي)
DATABASE_URL=sqlite:///archive.db

# PostgreSQL (محلي)
DATABASE_URL=postgresql://telegram_user:your_password@localhost:5432/telegram_archive

# PostgreSQL (خارجي)
DATABASE_URL=postgresql://username:password@your-server.com:5432/database_name

# MySQL (محلي)
DATABASE_URL=mysql://telegram_user:your_password@localhost:3306/telegram_archive

# MySQL (خارجي)
DATABASE_URL=mysql://username:password@your-server.com:3306/database_name
\`\`\`

## 🌐 قواعد البيانات السحابية

### Supabase (PostgreSQL):
\`\`\`env
DATABASE_URL=postgresql://postgres:your_password@db.your_project.supabase.co:5432/postgres
\`\`\`

### PlanetScale (MySQL):
\`\`\`env
DATABASE_URL=mysql://username:password@your-host.psdb.cloud/database_name?sslaccept=strict
\`\`\`

### Railway:
\`\`\`env
DATABASE_URL=postgresql://postgres:password@containers-us-west-xxx.railway.app:6543/railway
\`\`\`

### Heroku Postgres:
\`\`\`env
DATABASE_URL=postgres://user:password@host:5432/database
\`\`\`

## 🔍 اختبار الاتصال

\`\`\`bash
# اختبار البوت مع قاعدة البيانات
python run.py --diagnostics

# اختبار سريع
python run.py --test
\`\`\`

## 📊 مراقبة قاعدة البيانات

### PostgreSQL:
\`\`\`sql
-- الاتصال
psql -h localhost -U telegram_user -d telegram_archive

-- عرض الجداول
\dt

-- عرض الإحصائيات
SELECT COUNT(*) FROM archived_messages;

-- البحث
SELECT * FROM archived_messages WHERE content LIKE '%كلمة%' LIMIT 10;
\`\`\`

### MySQL:
\`\`\`sql
-- الاتصال
mysql -h localhost -u telegram_user -p telegram_archive

-- عرض الجداول
SHOW TABLES;

-- عرض الإحصائيات
SELECT COUNT(*) FROM archived_messages;

-- البحث
SELECT * FROM archived_messages WHERE MATCH(content) AGAINST('كلمة' IN NATURAL LANGUAGE MODE) LIMIT 10;
\`\`\`

## 🔒 نصائح الأمان

1. **استخدم كلمات مرور قوية**
2. **فعّل SSL للاتصالات الخارجية**
3. **قم بعمل نسخ احتياطية دورية**
4. **قيّد الوصول للمستخدمين المصرح لهم فقط**
5. **راقب استخدام الموارد**

## 🆘 حل المشاكل الشائعة

### خطأ الاتصال:
\`\`\`bash
# تحقق من حالة الخدمة
sudo systemctl status postgresql
sudo systemctl status mysql

# إعادة تشغيل الخدمة
sudo systemctl restart postgresql
sudo systemctl restart mysql
\`\`\`

### خطأ الصلاحيات:
\`\`\`sql
-- PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE telegram_archive TO telegram_user;

-- MySQL
GRANT ALL PRIVILEGES ON telegram_archive.* TO 'telegram_user'@'localhost';
\`\`\`

### خطأ الترميز:
\`\`\`sql
-- MySQL
ALTER DATABASE telegram_archive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

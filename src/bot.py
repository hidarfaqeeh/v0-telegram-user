#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أرشفة تليغرام - الفئة الرئيسية
"""

import asyncio
import os
import json
import sqlite3
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from dotenv import load_dotenv
    import aiofiles
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    print("🔧 قم بتشغيل: python run.py --setup")
    sys.exit(1)

# إعداد نظام السجلات
logger = logging.getLogger(__name__)

class TelegramArchiveBot:
    """فئة بوت أرشفة تليغرام الرئيسية"""
    
    def __init__(self, debug=False):
        """تهيئة البوت"""
        logger.info("🚀 بدء تهيئة بوت الأرشفة...")
        
        # تحميل المتغيرات البيئية
        self.load_environment()
        
        # إنشاء المجلدات المطلوبة
        self.create_directories()
        
        # إعداد قاعدة البيانات
        self.init_database()
        
        # متغيرات العملاء
        self.userbot = None
        self.bot_app = None
        self.is_running = False
        self.debug = debug
        
        logger.info("✅ تم تهيئة البوت بنجاح")

    def load_environment(self):
        """تحميل متغيرات البيئة"""
        # إنشاء ملف .env إذا لم يكن موجوداً
        if not Path('.env').exists():
            self.create_env_file()
        
        load_dotenv()
        
        # إعدادات Telethon (Userbot)
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone = os.getenv('PHONE_NUMBER')
        self.string_session = os.getenv('STRING_SESSION')
        
        # إعدادات Bot Token
        self.bot_token = os.getenv('BOT_TOKEN')
        
        # إعدادات القناة والمدراء
        self.source_channel = os.getenv('SOURCE_CHANNEL')
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        self.admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]
        
        # التحقق من المتغيرات المطلوبة
        self.validate_environment()

    def create_env_file(self):
        """إنشاء ملف .env تجريبي"""
        env_content = """# إعدادات Telethon (Userbot)
# احصل عليها من: https://my.telegram.org/apps
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890

# String Session (اختياري - يمكن استخدامه بدلاً من رقم الهاتف)
STRING_SESSION=your_string_session_here

# إعدادات Bot Token
# احصل عليه من: @BotFather
BOT_TOKEN=your_bot_token_here

# إعدادات القناة والمدراء
SOURCE_CHANNEL=@your_channel_username
ADMIN_IDS=123456789,987654321

# إعدادات إضافية
DEBUG=false
ENVIRONMENT=development
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.warning("📝 تم إنشاء ملف .env - يرجى تعديل القيم قبل التشغيل")

    def validate_environment(self):
        """التحقق من صحة متغيرات البيئة"""
        missing_vars = []
        
        if not self.api_id or self.api_id == 'your_api_id_here':
            missing_vars.append('API_ID')
        
        if not self.api_hash or self.api_hash == 'your_api_hash_here':
            missing_vars.append('API_HASH')
        
        if not self.bot_token or self.bot_token == 'your_bot_token_here':
            missing_vars.append('BOT_TOKEN')
        
        # التحقق من وجود String Session أو رقم الهاتف
        if not self.string_session or self.string_session == 'your_string_session_here':
            if not self.phone or self.phone == '+1234567890':
                missing_vars.append('STRING_SESSION أو PHONE_NUMBER')
        
        if missing_vars:
            logger.error(f"❌ متغيرات البيئة المفقودة: {', '.join(missing_vars)}")
            logger.error("يرجى تعديل ملف .env وإضافة القيم الصحيحة")
            logger.error("أو تشغيل: python run.py --session لإنشاء String Session")
            return False
        
        return True

    def create_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = ['archive', 'exports', 'backups', 'logs', 'config', 'sessions']
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        logger.info("📁 تم إنشاء المجلدات المطلوبة")

    def init_database(self):
        """إنشاء قاعدة البيانات وجداولها"""
        try:
            self.conn = sqlite3.connect('archive.db', check_same_thread=False)
            cursor = self.conn.cursor()
            
            # جدول الرسائل المؤرشفة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archived_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER,
                    date TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    content TEXT,
                    media_type TEXT,
                    file_id TEXT,
                    file_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id, channel_id)
                )
            ''')
            
            # جدول الإعدادات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول المدراء
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء فهارس للبحث السريع
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON archived_messages(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_content ON archived_messages(content)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_year_month_day ON archived_messages(year, month, day)')
            
            self.conn.commit()
            logger.info("✅ تم إعداد قاعدة البيانات بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
            raise

    async def start_userbot(self):
        """بدء تشغيل Userbot مع دعم String Session"""
        if not all([self.api_id, self.api_hash]):
            logger.error("❌ API_ID و API_HASH مطلوبان لتشغيل Userbot")
            return False
        
        try:
            # استخدام String Session إذا كان متوفراً
            if self.string_session and self.string_session != 'your_string_session_here':
                logger.info("🔐 استخدام String Session للاتصال...")
                session = StringSession(self.string_session)
            else:
                logger.info("📱 استخدام رقم الهاتف للاتصال...")
                session = 'sessions/userbot'
            
            self.userbot = TelegramClient(session, self.api_id, self.api_hash)
            
            # بدء الاتصال
            if self.string_session and self.string_session != 'your_string_session_here':
                await self.userbot.start()
            else:
                await self.userbot.start(phone=self.phone)
            
            # التحقق من الاتصال
            me = await self.userbot.get_me()
            logger.info(f"✅ تم تشغيل Userbot بنجاح - {me.first_name}")
            
            # إعداد مراقب الرسائل الجديدة
            if self.source_channel:
                @self.userbot.on(events.NewMessage(chats=self.source_channel))
                async def handle_new_message(event):
                    await self.archive_message(event.message)
                    logger.info(f"📥 تم أرشفة رسالة جديدة: {event.message.id}")
                
                logger.info(f"👀 بدء مراقبة القناة: {self.source_channel}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل Userbot: {e}")
            if "STRING_SESSION" in str(e) or "session" in str(e).lower():
                logger.error("💡 نصيحة: تشغيل python run.py --session لإنشاء String Session جديد")
            return False

    async def start_bot(self):
        """بدء تشغيل Bot"""
        if not self.bot_token:
            logger.error("❌ BOT_TOKEN مطلوب لتشغيل Bot")
            return False
        
        try:
            self.bot_app = Application.builder().token(self.bot_token).build()
            
            # إضافة معالجات الأوامر
            handlers = [
                CommandHandler("start", self.cmd_start),
                CommandHandler("help", self.cmd_help),
                CommandHandler("status", self.cmd_status),
                CommandHandler("archive_today", self.cmd_archive_today),
                CommandHandler("archive_day", self.cmd_archive_day),
                CommandHandler("browse", self.cmd_browse),
                CommandHandler("search", self.cmd_search),
                CommandHandler("export", self.cmd_export),
                CommandHandler("set_channel", self.cmd_set_channel),
                CommandHandler("diagnostics", self.cmd_diagnostics),
                CommandHandler("test_channel", self.cmd_test_channel),
                CommandHandler("channel_info", self.cmd_channel_info),
                CallbackQueryHandler(self.handle_callback),
            ]
            
            for handler in handlers:
                self.bot_app.add_handler(handler)
            
            logger.info("✅ تم إعداد Bot بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد Bot: {e}")
            return False

    def is_admin(self, user_id: int) -> bool:
        """التحقق من صلاحيات المدير"""
        return user_id in self.admin_ids

    async def archive_message(self, message):
        """أرشفة رسالة واحدة"""
        try:
            msg_date = message.date
            year = msg_date.year
            month = msg_date.month
            day = msg_date.day
            
            # تحضير بيانات الرسالة
            content = message.text or message.caption or ""
            media_type = None
            file_id = None
            file_name = None
            
            # معالجة الوسائط
            if message.media:
                if message.photo:
                    media_type = "photo"
                    file_id = str(message.photo.id)
                elif message.video:
                    media_type = "video"
                    file_id = str(message.video.id)
                    file_name = getattr(message.video, 'file_name', None)
                elif message.document:
                    media_type = "document"
                    file_id = str(message.document.id)
                    file_name = getattr(message.document, 'file_name', None)
                elif message.audio:
                    media_type = "audio"
                    file_id = str(message.audio.id)
                    file_name = getattr(message.audio, 'file_name', None)
            
            # حفظ في قاعدة البيانات
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO archived_messages 
                (message_id, channel_id, date, year, month, day, content, media_type, file_id, file_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.id,
                message.chat_id,
                msg_date.isoformat(),
                year, month, day,
                content,
                media_type,
                file_id,
                file_name
            ))
            self.conn.commit()
            
            # حفظ في ملف JSON
            await self.save_to_json_file(year, month, day, {
                'message_id': message.id,
                'date': msg_date.isoformat(),
                'content': content,
                'media_type': media_type,
                'file_id': file_id,
                'file_name': file_name
            })
            
        except Exception as e:
            logger.error(f"❌ خطأ في أرشفة الرسالة {message.id}: {e}")

    async def save_to_json_file(self, year: int, month: int, day: int, message_data: dict):
        """حفظ الرسالة في ملف JSON"""
        try:
            # إنشاء مسار الملف
            year_dir = Path('archive') / str(year)
            month_dir = year_dir / f"{month:02d}"
            month_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = month_dir / f"{day:02d}.json"
            
            # قراءة البيانات الموجودة
            messages = []
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            messages = json.loads(content)
                except (json.JSONDecodeError, FileNotFoundError):
                    messages = []
            
            # إضافة الرسالة الجديدة
            messages.append(message_data)
            
            # حفظ الملف
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ ملف JSON: {e}")

    # معالجات الأوامر
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ غير مصرح لك باستخدام هذا البوت")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="status")],
            [InlineKeyboardButton("📅 تصفح الأرشيف", callback_data="browse")],
            [InlineKeyboardButton("🔍 البحث", callback_data="search_menu")],
            [InlineKeyboardButton("⚙️ المساعدة", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 **مرحباً بك في بوت أرشفة تليغرام**

👋 أهلاً {update.effective_user.first_name}!

📋 **الوظائف المتاحة:**
• 🔄 أرشفة تلقائية للقناة المحددة
• 📅 أرشفة يدوية بتواريخ مخصصة  
• 🗂️ تصفح الأرشيف بطريقة تفاعلية
• 🔍 البحث في المحتوى المؤرشف
• 📤 تصدير واستيراد البيانات

📊 **الحالة الحالية:**
• القناة المصدر: `{self.source_channel or 'غير محددة'}`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}

اختر من القائمة أدناه للبدء:
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        help_text = """
🆘 **دليل استخدام البوت:**

**📁 أوامر الأرشفة:**
• `/archive_today` - أرشفة منشورات اليوم
• `/archive_day YYYY-MM-DD` - أرشفة يوم محدد

**📊 أوامر المعلومات:**
• `/status` - عرض إحصائيات الأرشيف
• `/browse` - تصفح الأرشيف تفاعلياً

**🔍 البحث:**
• `/search كلمة البحث` - البحث في المحتوى

**⚙️ الإدارة:**
• `/set_channel @channel` - تحديد القناة المصدر
• `/export YYYY-MM-DD` - تصدير أرشيف يوم
• `/diagnostics` - تشخيص البوت
• `/test_channel` - اختبار القناة
• `/channel_info` - معلومات القناة

**💡 نصائح:**
- استخدم الأزرار التفاعلية للتنقل السهل
- يمكن البحث في النصوص والتسميات التوضيحية
- الأرشفة التلقائية تعمل في الخلفية

**🔗 روابط مفيدة:**
- احصل على API من: https://my.telegram.org/apps
- أنشئ بوت جديد: @BotFather
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات الأرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        try:
            cursor = self.conn.cursor()
            
            # إجمالي الرسائل
            cursor.execute("SELECT COUNT(*) FROM archived_messages")
            total_messages = cursor.fetchone()[0]
            
            # رسائل اليوم
            today = datetime.now().date()
            cursor.execute(
                "SELECT COUNT(*) FROM archived_messages WHERE date LIKE ?",
                (f"{today}%",)
            )
            today_messages = cursor.fetchone()[0]
            
            # رسائل هذا الشهر
            this_month = today.strftime("%Y-%m")
            cursor.execute(
                "SELECT COUNT(*) FROM archived_messages WHERE date LIKE ?",
                (f"{this_month}%",)
            )
            month_messages = cursor.fetchone()[0]
            
            # أحدث رسالة
            cursor.execute(
                "SELECT date FROM archived_messages ORDER BY date DESC LIMIT 1"
            )
            latest = cursor.fetchone()
            latest_date = latest[0] if latest else "لا توجد رسائل"
            
            # حجم قاعدة البيانات
            db_size = Path('archive.db').stat().st_size / (1024 * 1024)  # MB
            
            status_text = f"""
📊 **إحصائيات الأرشيف:**

📈 **الرسائل:**
• إجمالي الرسائل: `{total_messages:,}`
• رسائل اليوم: `{today_messages:,}`
• رسائل هذا الشهر: `{month_messages:,}`

🕐 **التوقيت:**
• آخر رسالة مؤرشفة: `{latest_date}`
• وقت التحديث: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

⚙️ **النظام:**
• القناة المصدر: `{self.source_channel or 'غير محددة'}`
• حجم قاعدة البيانات: `{db_size:.2f} MB`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}
• Bot: {'🟢 يعمل' if self.is_running else '🔴 متوقف'}
            """
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في جلب الإحصائيات: {e}")

    async def cmd_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تشخيص سريع للبوت"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("🔍 جاري تشخيص البوت...")
        
        # تشخيص أساسي
        report = "📊 **تقرير التشخيص السريع:**\n\n"
        
        # فحص متغيرات البيئة
        env_check = "✅" if self.validate_environment() else "❌"
        report += f"{env_check} **متغيرات البيئة:** {'صحيحة' if env_check == '✅' else 'ناقصة'}\n"
        
        # فحص Userbot
        userbot_check = "✅" if self.userbot and self.userbot.is_connected() else "❌"
        report += f"{userbot_check} **Userbot:** {'متصل' if userbot_check == '✅' else 'غير متصل'}\n"
        
        # فحص Bot
        bot_check = "✅" if self.bot_app else "❌"
        report += f"{bot_check} **Bot:** {'جاهز' if bot_check == '✅' else 'غير جاهز'}\n"
        
        # فحص قاعدة البيانات
        db_check = "✅" if self.conn else "❌"
        report += f"{db_check} **قاعدة البيانات:** {'متصلة' if db_check == '✅' else 'غير متصلة'}\n"
        
        # فحص القناة المصدر
        channel_check = "✅" if self.source_channel else "❌"
        report += f"{channel_check} **القناة المصدر:** {'محددة' if channel_check == '✅' else 'غير محددة'}\n"
        
        if env_check == "❌":
            report += "\n💡 **اقتراحات:**\n"
            report += "• تشغيل: `python run.py --session` لإنشاء String Session\n"
            report += "• تحقق من ملف .env وتأكد من صحة البيانات\n"
        
        await update.message.reply_text(report, parse_mode='Markdown')

    async def cmd_test_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختبار الاتصال بالقناة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.source_channel:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        await update.message.reply_text("🔍 جاري اختبار الاتصال بالقناة...")
        
        try:
            # اختبار الوصول للقناة
            entity = await self.userbot.get_entity(self.source_channel)
            
            # جلب آخر 5 رسائل للاختبار
            messages = []
            try:
                async for message in self.userbot.iter_messages(self.source_channel, limit=5):
                    messages.append({
                        'id': message.id,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'content': (message.text or message.caption or '[وسائط]')[:50] + '...' if (message.text or message.caption) else '[وسائط بدون نص]',
                        'media': 'نعم' if message.media else 'لا'
                    })
            except Exception as e:
                messages_error = f"❌ خطأ في جلب الرسائل: {e}"
            
            # تحضير التقرير
            report = f"""
🔍 **تقرير اختبار القناة:**

✅ **معلومات القناة:**
• الاسم: `{entity.title}`
• المعرف: `{entity.id}`
• النوع: `{type(entity).__name__}`
• المعرف المدخل: `{self.source_channel}`
• عدد الأعضاء: `{getattr(entity, 'participants_count', 'غير متوفر')}`

📊 **اختبار جلب الرسائل:**
• تم جلب: `{len(messages)}` رسالة من آخر 5 رسائل
• حالة الاتصال: ✅ متصل

📝 **آخر الرسائل:**
        """
            
            if messages:
                for i, msg in enumerate(messages, 1):
                    report += f"\n{i}. `{msg['date']}` - ID: `{msg['id']}`"
                    report += f"\n   📄 المحتوى: {msg['content']}"
                    report += f"\n   📎 وسائط: {msg['media']}"
            else:
                report += "\n❌ لا توجد رسائل أو لا يمكن الوصول إليها"
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **فشل في الاتصال بالقناة:**\n"
                f"• القناة: `{self.source_channel}`\n"
                f"• الخطأ: `{str(e)}`\n\n"
                f"💡 **الحلول المقترحة:**\n"
                f"• تأكد من أن الـ Userbot عضو في القناة\n"
                f"• تأكد من صحة معرف القناة\n"
                f"• تأكد من صلاحيات القراءة\n"
                f"• جرب استخدام معرف رقمي بدلاً من @username",
                parse_mode='Markdown'
            )

    async def cmd_channel_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات مفصلة عن القناة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.source_channel:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر")
            return
        
        try:
            entity = await self.userbot.get_entity(self.source_channel)
            
            # جلب معلومات مفصلة
            info = f"""
📺 **معلومات القناة المفصلة:**

🏷️ **الأساسيات:**
• الاسم: `{entity.title}`
• المعرف الرقمي: `{entity.id}`
• المعرف النصي: `{getattr(entity, 'username', 'غير متوفر')}`
• النوع: `{type(entity).__name__}`

👥 **العضوية:**
• عدد الأعضاء: `{getattr(entity, 'participants_count', 'غير متوفر')}`
• تاريخ الإنشاء: `{getattr(entity, 'date', 'غير متوفر')}`

🔒 **الخصوصية:**
• قناة عامة: `{'نعم' if getattr(entity, 'username', None) else 'لا'}`
• محدودة: `{'نعم' if getattr(entity, 'restricted', False) else 'لا'}`
• محققة: `{'نعم' if getattr(entity, 'verified', False) else 'لا'}`

📝 **الوصف:**
{getattr(entity, 'about', 'لا يوجد وصف') or 'لا يوجد وصف'}
        """
            
            await update.message.reply_text(info, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في جلب معلومات القناة: {e}")

    # باقي الأوامر (browse, search, archive_today, etc.) يمكن إضافتها هنا...
    async def cmd_browse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصفح الأرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("📂 ميزة التصفح قيد التطوير...")

    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """البحث في الأرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("🔍 ميزة البحث قيد التطوير...")

    async def cmd_archive_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة منشورات اليوم"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("📅 ميزة أرشفة اليوم قيد التطوير...")

    async def cmd_archive_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة يوم محدد"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("📅 ميزة أرشفة يوم محدد قيد التطوير...")

    async def cmd_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصدير أرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("📤 ميزة التصدير قيد التطوير...")

    async def cmd_set_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحديد القناة المصدر"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **استخدم:** `/set_channel @channel_username`\n"
                "**أو:** `/set_channel channel_id`\n"
                "**مثال:** `/set_channel @my_channel`",
                parse_mode='Markdown'
            )
            return
        
        channel = context.args[0]
        self.source_channel = channel
        
        # حفظ في قاعدة البيانات
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("source_channel", channel)
            )
            self.conn.commit()
            
            await update.message.reply_text(f"✅ تم تحديد القناة المصدر: **{channel}**", parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ الإعدادات: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            return
        
        data = query.data
        
        if data == "status":
            await query.edit_message_text("📊 الإحصائيات قيد التطوير...")
        elif data == "browse":
            await query.edit_message_text("📂 التصفح قيد التطوير...")
        elif data == "help":
            await query.edit_message_text("🆘 المساعدة قيد التطوير...")

    async def run(self):
        """تشغيل البوت الرئيسي"""
        logger.info("🚀 بدء تشغيل بوت الأرشفة...")
        
        # التحقق من متغيرات البيئة
        if not self.validate_environment():
            logger.error("❌ يرجى تعديل ملف .env وإضافة القيم الصحيحة")
            logger.error("💡 أو تشغيل: python run.py --session")
            return False
        
        self.is_running = True
        
        try:
            # بدء Userbot
            logger.info("🔄 بدء تشغيل Userbot...")
            userbot_success = await self.start_userbot()
            
            if not userbot_success:
                logger.warning("⚠️ فشل في تشغيل Userbot - ستعمل الأوامر اليدوية فقط")
                logger.warning("💡 تشغيل: python run.py --session لإنشاء String Session")
            
            # بدء Bot
            logger.info("🔄 بدء تشغيل Bot...")
            bot_success = await self.start_bot()
            
            if not bot_success:
                logger.error("❌ فشل في تشغيل Bot")
                return False
            
            logger.info("✅ تم تشغيل البوت بنجاح!")
            logger.info("📱 Userbot: " + ("متصل ويراقب الرسائل الجديدة" if userbot_success else "غير متصل"))
            logger.info("🤖 Bot: جاهز لاستقبال الأوامر")
            
            # تشغيل Bot
            await self.bot_app.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
            
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        finally:
            self.is_running = False
            if self.userbot:
                await self.userbot.disconnect()
            if self.conn:
                self.conn.close()
            logger.info("🔚 تم إغلاق البوت")

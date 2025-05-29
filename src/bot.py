#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أرشفة تليغرام - الفئة الرئيسية المحسنة
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

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import Config
from utils.logger import setup_logging

logger = setup_logging()

class TelegramArchiveBot:
    """فئة بوت أرشفة تليغرام الرئيسية المحسنة"""
    
    def __init__(self, debug=False):
        """تهيئة البوت"""
        logger.info("🚀 بدء تهيئة بوت الأرشفة المحسن...")
        
        # وضع التصحيح
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("🐞 تم تفعيل وضع التصحيح")
        
        # تحميل الإعدادات
        self.config = Config()
        
        # إنشاء المجلدات المطلوبة
        self.create_directories()
        
        # إعداد قاعدة البيانات المحسنة
        self.init_database()
        
        # متغيرات العملاء
        self.userbot = None
        self.bot_app = None
        self.is_running = False
        
        # متغيرات التصفح
        self.user_sessions = {}  # لحفظ جلسات التصفح للمستخدمين
        
        logger.info("✅ تم تهيئة البوت المحسن بنجاح")

    def create_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = ['archive', 'exports', 'backups', 'logs', 'config', 'sessions', 'media']
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        logger.info("📁 تم إنشاء المجلدات المطلوبة")

    def init_database(self):
        """إنشاء قاعدة البيانات المحسنة وجداولها"""
        try:
            self.conn = sqlite3.connect('archive.db', check_same_thread=False)
            cursor = self.conn.cursor()
            
            # جدول الرسائل المؤرشفة المحسن
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
                    file_size INTEGER,
                    file_path TEXT,
                    views INTEGER DEFAULT 0,
                    forwards INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    reactions TEXT,
                    edit_date TEXT,
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
            
            # جدول جلسات التصفح
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS browse_sessions (
                    user_id INTEGER PRIMARY KEY,
                    current_year INTEGER,
                    current_month INTEGER,
                    current_day INTEGER,
                    current_index INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء فهارس محسنة للبحث السريع
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON archived_messages(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_content ON archived_messages(content)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_year_month_day ON archived_messages(year, month, day)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_type ON archived_messages(media_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON archived_messages(message_id)')
            
            self.conn.commit()
            logger.info("✅ تم إعداد قاعدة البيانات المحسنة بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
            raise

    async def start_userbot(self):
        """بدء تشغيل Userbot مع دعم String Session"""
        if not all([self.config.API_ID, self.config.API_HASH]):
            logger.error("❌ API_ID و API_HASH مطلوبان لتشغيل Userbot")
            return False
        
        try:
            # استخدام String Session إذا كان متوفراً
            if self.config.STRING_SESSION:
                logger.info("🔐 استخدام String Session للاتصال...")
                session = StringSession(self.config.STRING_SESSION)
            else:
                logger.info("📱 استخدام رقم الهاتف للاتصال...")
                session = 'sessions/userbot'
            
            self.userbot = TelegramClient(session, self.config.API_ID, self.config.API_HASH)
            
            # بدء الاتصال
            if self.config.STRING_SESSION:
                await self.userbot.start()
            else:
                await self.userbot.start(phone=self.config.PHONE_NUMBER)
            
            # التحقق من الاتصال
            me = await self.userbot.get_me()
            logger.info(f"✅ تم تشغيل Userbot بنجاح - {me.first_name}")
            
            # إعداد مراقب الرسائل الجديدة
            if self.config.SOURCE_CHANNEL:
                @self.userbot.on(events.NewMessage(chats=self.config.SOURCE_CHANNEL))
                async def handle_new_message(event):
                    await self.archive_message(event.message)
                    logger.info(f"📥 تم أرشفة رسالة جديدة: {event.message.id}")
                
                logger.info(f"👀 بدء مراقبة القناة: {self.config.SOURCE_CHANNEL}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل Userbot: {e}")
            if "STRING_SESSION" in str(e) or "session" in str(e).lower():
                logger.error("💡 نصيحة: تشغيل python run.py --session لإنشاء String Session جديد")
            return False

    async def start_bot(self):
        """بدء تشغيل Bot"""
        if not self.config.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN مطلوب لتشغيل Bot")
            return False
        
        try:
            self.bot_app = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # إضافة معالجات الأوامر المحسنة
            handlers = [
                CommandHandler("start", self.cmd_start),
                CommandHandler("help", self.cmd_help),
                CommandHandler("status", self.cmd_status),
                CommandHandler("archive_today", self.cmd_archive_today),
                CommandHandler("archive_day", self.cmd_archive_day),
                CommandHandler("archive_month", self.cmd_archive_month),
                CommandHandler("archive_year", self.cmd_archive_year),
                CommandHandler("archive_range", self.cmd_archive_range),
                CommandHandler("archive_all", self.cmd_archive_all),
                CommandHandler("browse", self.cmd_browse),
                CommandHandler("search", self.cmd_search),
                CommandHandler("view_post", self.cmd_view_post),
                CommandHandler("export", self.cmd_export),
                CommandHandler("set_channel", self.cmd_set_channel),
                CommandHandler("diagnostics", self.cmd_diagnostics),
                CallbackQueryHandler(self.handle_callback),
            ]
            
            for handler in handlers:
                self.bot_app.add_handler(handler)
            
            logger.info("✅ تم إعداد Bot المحسن بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد Bot: {e}")
            return False

    async def archive_message(self, message):
        """أرشفة رسالة واحدة مع معلومات محسنة"""
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
            file_size = None
            file_path = None
            
            # معالجة الوسائط المحسنة
            if message.media:
                if message.photo:
                    media_type = "photo"
                    file_id = str(message.photo.id)
                    file_size = getattr(message.photo, 'file_size', 0)
                elif message.video:
                    media_type = "video"
                    file_id = str(message.video.id)
                    file_name = getattr(message.video, 'file_name', None)
                    file_size = getattr(message.video, 'file_size', 0)
                elif message.document:
                    media_type = "document"
                    file_id = str(message.document.id)
                    file_name = getattr(message.document, 'file_name', None)
                    file_size = getattr(message.document, 'file_size', 0)
                elif message.audio:
                    media_type = "audio"
                    file_id = str(message.audio.id)
                    file_name = getattr(message.audio, 'file_name', None)
                    file_size = getattr(message.audio, 'file_size', 0)
                elif message.voice:
                    media_type = "voice"
                    file_id = str(message.voice.id)
                    file_size = getattr(message.voice, 'file_size', 0)
                elif message.sticker:
                    media_type = "sticker"
                    file_id = str(message.sticker.id)
                    file_size = getattr(message.sticker, 'file_size', 0)
            
            # معلومات إضافية
            views = getattr(message, 'views', 0)
            forwards = getattr(message, 'forwards', 0)
            replies = getattr(message, 'replies', 0)
            edit_date = getattr(message, 'edit_date', None)
            edit_date_str = edit_date.isoformat() if edit_date else None
            
            # معالجة التفاعلات
            reactions = None
            if hasattr(message, 'reactions') and message.reactions:
                reactions = json.dumps([{
                    'reaction': str(reaction.reaction),
                    'count': reaction.count
                } for reaction in message.reactions.results])
            
            # حفظ في قاعدة البيانات
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO archived_messages 
                (message_id, channel_id, date, year, month, day, content, media_type, 
                 file_id, file_name, file_size, file_path, views, forwards, replies, 
                 reactions, edit_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.id,
                message.chat_id,
                msg_date.isoformat(),
                year, month, day,
                content,
                media_type,
                file_id,
                file_name,
                file_size,
                file_path,
                views,
                forwards,
                replies,
                reactions,
                edit_date_str
            ))
            self.conn.commit()
            
            # حفظ في ملف JSON المحسن
            await self.save_to_json_file(year, month, day, {
                'message_id': message.id,
                'date': msg_date.isoformat(),
                'content': content,
                'media_type': media_type,
                'file_id': file_id,
                'file_name': file_name,
                'file_size': file_size,
                'views': views,
                'forwards': forwards,
                'replies': replies,
                'reactions': reactions,
                'edit_date': edit_date_str
            })
            
        except Exception as e:
            logger.error(f"❌ خطأ في أرشفة الرسالة {message.id}: {e}")

    async def save_to_json_file(self, year: int, month: int, day: int, message_data: dict):
        """حفظ الرسالة في ملف JSON محسن"""
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
                            data = json.loads(content)
                            messages = data.get('messages', [])
                except (json.JSONDecodeError, FileNotFoundError):
                    messages = []
            
            # إضافة الرسالة الجديدة
            messages.append(message_data)
            
            # إنشاء هيكل محسن للملف
            file_data = {
                'date': f"{year}-{month:02d}-{day:02d}",
                'total_messages': len(messages),
                'last_updated': datetime.now().isoformat(),
                'messages': messages
            }
            
            # حفظ الملف
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ ملف JSON: {e}")

    def is_admin(self, user_id: int) -> bool:
        """التحقق من صلاحيات المدير"""
        return user_id in self.config.ADMIN_IDS

    # معالجات الأوامر المحسنة
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية المحسن"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ غير مصرح لك باستخدام هذا البوت")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="status")],
            [InlineKeyboardButton("📅 تصفح الأرشيف", callback_data="browse")],
            [InlineKeyboardButton("🔍 البحث", callback_data="search_menu")],
            [InlineKeyboardButton("📁 الأرشفة", callback_data="archive_menu")],
            [InlineKeyboardButton("⚙️ المساعدة", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 **مرحباً بك في بوت أرشفة تليغرام المحسن**

👋 أهلاً {update.effective_user.first_name}!

✨ **الميزات الجديدة:**
• 🖼️ عرض الوسائط (صور، فيديوهات، ملفات)
• ⏭️ التنقل بين المنشورات
• 📊 إحصائيات مفصلة
• 🔄 أرشفة نطاقات زمنية كبيرة
• 💾 حفظ محسن مع معلومات إضافية

📋 **الوظائف المتاحة:**
• 🔄 أرشفة تلقائية للقناة المحددة
• 📅 أرشفة يدوية بتواريخ مخصصة  
• 🗂️ تصفح الأرشيف بطريقة تفاعلية
• 🔍 البحث في المحتوى المؤرشف
• 📤 تصدير واستيراد البيانات

📊 **الحالة الحالية:**
• القناة المصدر: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}

اختر من القائمة أدناه للبدء:
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة المحسن"""
        if not self.is_admin(update.effective_user.id):
            return
        
        help_text = """
🆘 **دليل استخدام البوت المحسن:**

**📁 أوامر الأرشفة:**
• `/archive_today` - أرشفة منشورات اليوم
• `/archive_day YYYY-MM-DD` - أرشفة يوم محدد
• `/archive_month YYYY-MM` - أرشفة شهر كامل
• `/archive_year YYYY` - أرشفة سنة كاملة
• `/archive_range تاريخ_البداية تاريخ_النهاية` - أرشفة نطاق مخصص
• `/archive_all` - أرشفة جميع المنشورات (تحذير!)

**📊 أوامر المعلومات:**
• `/status` - عرض إحصائيات الأرشيف
• `/browse` - تصفح الأرشيف تفاعلياً (محسن!)
• `/view_post message_id` - عرض منشور بالتفصيل

**🔍 البحث:**
• `/search كلمة البحث` - البحث في المحتوى

**⚙️ الإدارة:**
• `/set_channel @channel` - تحديد القناة المصدر
• `/export YYYY-MM-DD` - تصدير أرشيف يوم
• `/diagnostics` - تشخيص مشاكل البوت

**✨ الميزات الجديدة:**
• 🖼️ عرض الوسائط (صور، فيديوهات، ملفات)
• ⏭️ التنقل بين المنشورات (السابق/التالي)
• 📊 إحصائيات مفصلة لكل منشور
• 🔄 أرشفة نطاقات زمنية كبيرة
• 💾 حفظ محسن مع معلومات إضافية

**💡 نصائح:**
- استخدم الأزرار التفاعلية للتنقل السهل
- الأرشفة التلقائية تعمل في الخلفية
- يمكن عرض الوسائط مع النصوص
- التنقل بين المنشورات سهل وسريع

**🔗 روابط مفيدة:**
- احصل على API من: https://my.telegram.org/apps
- أنشئ بوت جديد: @BotFather
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def cmd_archive_month(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة شهر كامل"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📅 **استخدم:** `/archive_month YYYY-MM`\n"
                "**مثال:** `/archive_month 2024-05`",
                parse_mode='Markdown'
            )
            return
        
        try:
            month_str = context.args[0]
            year, month = map(int, month_str.split('-'))
            
            # تحديد بداية ونهاية الشهر
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            await update.message.reply_text(f"🔄 جاري أرشفة شهر **{month_str}**...\n⏳ قد يستغرق هذا وقتاً طويلاً", parse_mode='Markdown')
            
            count = await self.archive_date_range_with_progress(start_date, end_date, update)
            await update.message.reply_text(f"✅ تم أرشفة **{count}** رسالة من شهر **{month_str}**", parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق التاريخ غير صحيح. استخدم: **YYYY-MM**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def cmd_archive_year(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة سنة كاملة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📅 **استخدم:** `/archive_year YYYY`\n"
                "**مثال:** `/archive_year 2024`",
                parse_mode='Markdown'
            )
            return
        
        try:
            year = int(context.args[0])
            
            # تحديد بداية ونهاية السنة
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
            
            # تحذير للمستخدم
            await update.message.reply_text(
                f"⚠️ **تحذير:** ستتم أرشفة سنة كاملة ({year})\n"
                f"🕐 قد يستغرق هذا ساعات أو أيام حسب حجم البيانات\n"
                f"📊 هل تريد المتابعة؟",
                parse_mode='Markdown'
            )
            
            # يمكن إضافة تأكيد هنا
            await update.message.reply_text(f"🔄 جاري أرشفة سنة **{year}**...\n⏳ سيتم إرسال تحديثات دورية", parse_mode='Markdown')
            
            count = await self.archive_date_range_with_progress(start_date, end_date, update)
            await update.message.reply_text(f"✅ تم أرشفة **{count}** رسالة من سنة **{year}**", parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق السنة غير صحيح. استخدم: **YYYY**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def cmd_archive_range(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة نطاق زمني مخصص"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        if len(context.args) != 2:
            await update.message.reply_text(
                "📅 **استخدم:** `/archive_range تاريخ_البداية تاريخ_النهاية`\n"
                "**مثال:** `/archive_range 2024-01-01 2024-03-31`",
                parse_mode='Markdown'
            )
            return
        
        try:
            start_str, end_str = context.args
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            
            if start_date > end_date:
                await update.message.reply_text("❌ تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
                return
            
            days_diff = (end_date - start_date).days + 1
            await update.message.reply_text(
                f"🔄 جاري أرشفة **{days_diff}** يوم من **{start_str}** إلى **{end_str}**...\n"
                f"⏳ قد يستغرق هذا وقتاً طويلاً",
                parse_mode='Markdown'
            )
            
            count = await self.archive_date_range_with_progress(start_date, end_date, update)
            await update.message.reply_text(
                f"✅ تم أرشفة **{count}** رسالة من **{start_str}** إلى **{end_str}**",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق التاريخ غير صحيح. استخدم: **YYYY-MM-DD**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def cmd_archive_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة جميع المنشورات في القناة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        # تحذير قوي
        warning_text = """
⚠️ **تحذير شديد!**

أنت على وشك أرشفة **جميع المنشورات** في القناة!

🚨 **المخاطر:**
• قد يستغرق ساعات أو أيام
• استهلاك كبير للموارد
• قد يؤثر على أداء الخادم

💡 **البدائل المقترحة:**
• `/archive_year 2024` - أرشفة سنة محددة
• `/archive_range تاريخ_البداية تاريخ_النهاية` - نطاق محدد

❓ هل أنت متأكد من المتابعة؟
        """
        
        await update.message.reply_text(warning_text, parse_mode='Markdown')
        
        # يمكن إضافة نظام تأكيد هنا
        # للآن سنتابع مع تحذير إضافي
        
        await update.message.reply_text("🔄 جاري أرشفة **جميع المنشورات**...\n⏳ سيتم إرسال تحديثات دورية", parse_mode='Markdown')
        
        try:
            count = 0
            progress_message = None
            
            async for message in self.userbot.iter_messages(self.config.SOURCE_CHANNEL):
                await self.archive_message(message)
                count += 1
                
                # تحديث كل 500 رسالة
                if count % 500 == 0:
                    if progress_message:
                        try:
                            await progress_message.edit_text(f"📊 تم أرشفة **{count:,}** رسالة...", parse_mode='Markdown')
                        except:
                            pass
                    else:
                        progress_message = await update.message.reply_text(f"📊 تم أرشفة **{count:,}** رسالة...", parse_mode='Markdown')
                    
                    logger.info(f"📊 تم أرشفة {count:,} رسالة...")
            
            await update.message.reply_text(f"✅ تم أرشفة **{count:,}** رسالة من جميع المنشورات!", parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def archive_date_range_with_progress(self, start_date, end_date, update) -> int:
        """أرشفة نطاق من التواريخ مع عرض التقدم"""
        if not self.userbot or not self.config.SOURCE_CHANNEL:
            return 0
        
        count = 0
        progress_message = None
        
        try:
            async for message in self.userbot.iter_messages(
                self.config.SOURCE_CHANNEL,
                offset_date=end_date + timedelta(days=1),
                reverse=True
            ):
                if message.date.date() < start_date:
                    break
                if message.date.date() <= end_date:
                    await self.archive_message(message)
                    count += 1
                    
                    # تحديث كل 100 رسالة
                    if count % 100 == 0:
                        if progress_message:
                            try:
                                await progress_message.edit_text(f"📊 تم أرشفة **{count:,}** رسالة...", parse_mode='Markdown')
                            except:
                                pass
                        else:
                            progress_message = await update.message.reply_text(f"📊 تم أرشفة **{count:,}** رسالة...", parse_mode='Markdown')
                        
                        logger.info(f"📊 تم أرشفة {count:,} رسالة...")
                        
        except Exception as e:
            logger.error(f"❌ خطأ في أرشفة النطاق: {e}")
        
        return count

    async def cmd_view_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض منشور محدد بالتفصيل"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **استخدم:** `/view_post message_id`\n"
                "**مثال:** `/view_post 12345`",
                parse_mode='Markdown'
            )
            return
        
        try:
            message_id = int(context.args[0])
            
            # البحث عن المنشور في قاعدة البيانات
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT * FROM archived_messages WHERE message_id = ? LIMIT 1""",
                (message_id,)
            )
            
            row = cursor.fetchone()
            
            if not row:
                await update.message.reply_text(f"❌ لم يتم العثور على المنشور رقم **{message_id}**", parse_mode='Markdown')
                return
            
            # عرض المنشور بالتفصيل
            await self.display_message_detailed(update, row, 0, 1)
            
        except ValueError:
            await update.message.reply_text("❌ معرف المنشور يجب أن يكون رقماً")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في عرض المنشور: {e}")

    async def display_message_detailed(self, update, message_row, current_index, total_messages):
        """عرض رسالة بالتفصيل مع الوسائط"""
        try:
            # استخراج بيانات الرسالة
            (id, message_id, channel_id, date, year, month, day, content, 
             media_type, file_id, file_name, file_size, file_path, views, 
             forwards, replies, reactions, edit_date, created_at) = message_row
            
            # تحضير النص
            message_text = f"""
📝 **منشور رقم {message_id}**

📅 **التاريخ:** `{date[:19]}`
🕐 **وقت الأرشفة:** `{created_at[:19]}`

📊 **الإحصائيات:**
• 👀 المشاهدات: `{views or 0:,}`
• 🔄 الإعادات: `{forwards or 0:,}`
• 💬 الردود: `{replies or 0:,}`

📍 **الموقع:** `{current_index + 1}/{total_messages}`
            """
            
            # إضافة معلومات التعديل
            if edit_date:
                message_text += f"\n✏️ **آخر تعديل:** `{edit_date[:19]}`"
            
            # إضافة معلومات الملف
            if media_type:
                message_text += f"\n\n📎 **الوسائط:**\n• النوع: `{media_type}`"
                if file_name:
                    message_text += f"\n• الاسم: `{file_name}`"
                if file_size:
                    size_mb = file_size / (1024 * 1024)
                    if size_mb >= 1:
                        message_text += f"\n• الحجم: `{size_mb:.2f} MB`"
                    else:
                        size_kb = file_size / 1024
                        message_text += f"\n• الحجم: `{size_kb:.2f} KB`"
            
            # إضافة المحتوى
            if content:
                preview = content[:500] + "..." if len(content) > 500 else content
                message_text += f"\n\n📄 **المحتوى:**\n{preview}"
            
            # إضافة التفاعلات
            if reactions:
                try:
                    reactions_data = json.loads(reactions)
                    if reactions_data:
                        message_text += f"\n\n😊 **التفاعلات:**"
                        for reaction in reactions_data[:5]:  # أول 5 تفاعلات
                            message_text += f"\n• {reaction['reaction']}: {reaction['count']}"
                except:
                    pass
            
            # أزرار التنقل
            keyboard = []
            nav_buttons = []
            
            if current_index > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"nav_prev_{current_index}"))
            
            if current_index < total_messages - 1:
                nav_buttons.append(InlineKeyboardButton("➡️ التالي", callback_data=f"nav_next_{current_index}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            # أزرار إضافية
            keyboard.append([
                InlineKeyboardButton("🔍 البحث", callback_data="search_menu"),
                InlineKeyboardButton("📅 التصفح", callback_data="browse")
            ])
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # إرسال الرسالة
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
            # إرسال الوسائط إذا كانت متوفرة
            if media_type and file_id:
                await self.send_media_if_available(update, media_type, file_id, file_name)
                
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الرسالة: {e}")
            error_text = f"❌ خطأ في عرض المنشور: {e}"
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_text)
            else:
                await update.message.reply_text(error_text)

    async def send_media_if_available(self, update, media_type, file_id, file_name):
        """إرسال الوسائط إذا كانت متوفرة"""
        try:
            # محاولة إرسال الوسائط باستخدام file_id
            chat_id = update.effective_chat.id
            
            if media_type == "photo":
                await self.bot_app.bot.send_photo(chat_id=chat_id, photo=file_id)
            elif media_type == "video":
                await self.bot_app.bot.send_video(chat_id=chat_id, video=file_id)
            elif media_type == "document":
                await self.bot_app.bot.send_document(chat_id=chat_id, document=file_id)
            elif media_type == "audio":
                await self.bot_app.bot.send_audio(chat_id=chat_id, audio=file_id)
            elif media_type == "voice":
                await self.bot_app.bot.send_voice(chat_id=chat_id, voice=file_id)
            elif media_type == "sticker":
                await self.bot_app.bot.send_sticker(chat_id=chat_id, sticker=file_id)
                
        except Exception as e:
            logger.warning(f"⚠️ لم يتم إرسال الوسائط: {e}")
            # إرسال رسالة بديلة
            media_info = f"📎 **الوسائط غير متوفرة**\n• النوع: `{media_type}`"
            if file_name:
                media_info += f"\n• الاسم: `{file_name}`"
            
            if hasattr(update, 'callback_query') and update.callback_query:
                await self.bot_app.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=media_info,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(media_info, parse_mode='Markdown')

    # باقي الدوال ستكون في الجزء التالي...
    async def run(self):
        """تشغيل البوت الرئيسي"""
        logger.info("🚀 بدء تشغيل بوت الأرشفة المحسن...")
        
        # التحقق من الإعدادات
        if not self.config.validate():
            logger.error("❌ يرجى تعديل ملف .env وإضافة القيم الصحيحة")
            logger.error("💡 أو تشغيل: python run.py --setup")
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
            
            logger.info("✅ تم تشغيل البوت المحسن بنجاح!")
            logger.info("📱 Userbot: " + ("متصل ويراقب الرسائل الجديدة" if userbot_success else "غير متصل"))
            logger.info("🤖 Bot: جاهز لاستقبال الأوامر")
            
            # تشغيل Bot بطريقة محسنة
            async with self.bot_app:
                await self.bot_app.start()
                await self.bot_app.updater.start_polling(drop_pending_updates=True)
                
                # انتظار إيقاف البوت
                try:
                    await asyncio.Event().wait()
                except (KeyboardInterrupt, asyncio.CancelledError):
                    logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
                finally:
                    await self.bot_app.updater.stop()
                    await self.bot_app.stop()
            
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
            if self.debug:
                import traceback
                logger.error(traceback.format_exc())
        finally:
            self.is_running = False
            if self.userbot:
                await self.userbot.disconnect()
            if self.conn:
                self.conn.close()
            logger.info("🔚 تم إغلاق البوت")

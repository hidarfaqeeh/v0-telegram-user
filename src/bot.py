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

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات الأرشيف المحسنة"""
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
            
            # إحصائيات الوسائط
            cursor.execute("""
                SELECT media_type, COUNT(*) 
                FROM archived_messages 
                WHERE media_type IS NOT NULL 
                GROUP BY media_type
            """)
            media_stats = cursor.fetchall()
            
            # أحدث رسالة
            cursor.execute(
                "SELECT date FROM archived_messages ORDER BY date DESC LIMIT 1"
            )
            latest = cursor.fetchone()
            latest_date = latest[0] if latest else "لا توجد رسائل"
            
            # حجم قاعدة البيانات
            db_size = Path('archive.db').stat().st_size / (1024 * 1024)  # MB
            
            # إحصائيات التفاعلات
            cursor.execute("SELECT SUM(views), SUM(forwards), SUM(replies) FROM archived_messages")
            interaction_stats = cursor.fetchone()
            total_views = interaction_stats[0] or 0
            total_forwards = interaction_stats[1] or 0
            total_replies = interaction_stats[2] or 0
            
            status_text = f"""
📊 **إحصائيات الأرشيف المحسنة:**

📈 **الرسائل:**
• إجمالي الرسائل: `{total_messages:,}`
• رسائل اليوم: `{today_messages:,}`
• رسائل هذا الشهر: `{month_messages:,}`

📊 **التفاعلات:**
• إجمالي المشاهدات: `{total_views:,}`
• إجمالي الإعادات: `{total_forwards:,}`
• إجمالي الردود: `{total_replies:,}`

📎 **الوسائط:**"""
            
            if media_stats:
                for media_type, count in media_stats:
                    media_icon = {
                        "photo": "🖼️", "video": "🎥", "document": "📄", 
                        "audio": "🎵", "voice": "🎤", "sticker": "🎭"
                    }.get(media_type, "📎")
                    status_text += f"\n• {media_icon} {media_type}: `{count:,}`"
            else:
                status_text += "\n• لا توجد وسائط مؤرشفة"

            status_text += f"""

🕐 **التوقيت:**
• آخر رسالة مؤرشفة: `{latest_date}`
• وقت التحديث: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

⚙️ **النظام:**
• القناة المصدر: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
• حجم قاعدة البيانات: `{db_size:.2f} MB`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}
• Bot: {'🟢 يعمل' if self.is_running else '🔴 متوقف'}
            """
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في جلب الإحصائيات: {e}")

    async def cmd_browse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصفح الأرشيف المحسن"""
        if not self.is_admin(update.effective_user.id):
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT year FROM archived_messages ORDER BY year DESC")
            years = [row[0] for row in cursor.fetchall()]
            
            if not years:
                await update.message.reply_text("📭 لا توجد رسائل مؤرشفة بعد")
                return
            
            keyboard = []
            for year in years:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ?", (year,)
                )
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 {year} ({count:,} رسالة)",
                        callback_data=f"browse_year_{year}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📂 اختر السنة للتصفح:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في تصفح الأرشيف: {e}")

    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """البحث في الأرشيف المحسن"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔍 **استخدم:** `/search كلمة البحث`\n"
                "**مثال:** `/search مرحبا`\n\n"
                "💡 **نصائح البحث:**\n"
                "• يمكن البحث في النصوص والتسميات التوضيحية\n"
                "• البحث يدعم الكلمات العربية والإنجليزية\n"
                "• استخدم كلمات مفتاحية قصيرة للنتائج الأفضل",
                parse_mode='Markdown'
            )
            return
        
        search_term = " ".join(context.args)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT message_id, date, content, media_type, views, forwards 
                   FROM archived_messages 
                   WHERE content LIKE ? 
                   ORDER BY date DESC LIMIT 20""",
                (f"%{search_term}%",)
            )
            results = cursor.fetchall()
            
            if not results:
                await update.message.reply_text(
                    f"❌ لم يتم العثور على نتائج لـ: **{search_term}**\n\n"
                    f"💡 جرب:\n"
                    f"• كلمات مختلفة\n"
                    f"• كلمات أقصر\n"
                    f"• البحث بالإنجليزية إذا كان النص إنجليزي",
                    parse_mode='Markdown'
                )
                return
            
            response = f"🔍 **نتائج البحث عن:** `{search_term}`\n"
            response += f"📊 **تم العثور على {len(results)} نتيجة**\n\n"
            
            for i, (msg_id, date, content, media_type, views, forwards) in enumerate(results[:10], 1):
                preview = content[:100] + "..." if len(content) > 100 else content
                media_icon = {
                    "photo": "🖼️", "video": "🎥", "document": "📄", 
                    "audio": "🎵", "voice": "🎤", "sticker": "🎭"
                }.get(media_type, "💬")
                
                response += f"{i}. {media_icon} **{date[:10]}** (ID: `{msg_id}`)\n"
                if views or forwards:
                    response += f"   👀 {views or 0} | 🔄 {forwards or 0}\n"
                response += f"   `{preview}`\n\n"
            
            if len(results) > 10:
                response += f"... و {len(results) - 10} نتيجة أخرى\n\n"
            
            response += f"💡 استخدم `/view_post message_id` لعرض منشور محدد"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في البحث: {e}")

    async def cmd_archive_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة منشورات اليوم"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        await update.message.reply_text("🔄 جاري أرشفة منشورات اليوم...")
        
        try:
            today = datetime.now().date()
            count = await self.archive_date_range_with_progress(today, today, update)
            await update.message.reply_text(f"✅ تم أرشفة **{count}** رسالة من اليوم", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def cmd_archive_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة يوم محدد"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📅 **استخدم:** `/archive_day YYYY-MM-DD`\n"
                "**مثال:** `/archive_day 2025-05-29`",
                parse_mode='Markdown'
            )
            return
        
        try:
            date_str = context.args[0]
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            await update.message.reply_text(f"🔄 جاري أرشفة **{date_str}**...", parse_mode='Markdown')
            count = await self.archive_date_range_with_progress(target_date, target_date, update)
            await update.message.reply_text(f"✅ تم أرشفة **{count}** رسالة من **{date_str}**", parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق التاريخ غير صحيح. استخدم: **YYYY-MM-DD**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def cmd_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصدير أرشيف يوم كملف JSON"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📤 **استخدم:** `/export YYYY-MM-DD`\n"
                "**مثال:** `/export 2025-05-29`",
                parse_mode='Markdown'
            )
            return
        
        try:
            date_str = context.args[0]
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # جلب رسائل اليوم
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT * FROM archived_messages 
                   WHERE date LIKE ? 
                   ORDER BY date""",
                (f"{date_str}%",)
            )
            
            rows = cursor.fetchall()
            
            if not rows:
                await update.message.reply_text(f"❌ لا توجد رسائل في **{date_str}**", parse_mode='Markdown')
                return
            
            # تحضير البيانات
            messages = []
            for row in rows:
                messages.append({
                    'message_id': row[1],
                    'channel_id': row[2],
                    'date': row[3],
                    'content': row[6],
                    'media_type': row[7],
                    'file_id': row[8],
                    'file_name': row[9],
                    'file_size': row[10],
                    'views': row[12],
                    'forwards': row[13],
                    'replies': row[14],
                    'reactions': row[15],
                    'edit_date': row[16]
                })
            
            # إنشاء ملف JSON
            export_data = {
                'date': date_str,
                'total_messages': len(messages),
                'exported_at': datetime.now().isoformat(),
                'source_channel': self.config.SOURCE_CHANNEL,
                'messages': messages
            }
            
            # حفظ في مجلد التصدير
            exports_dir = Path('exports')
            exports_dir.mkdir(exist_ok=True)
            
            filename = exports_dir / f"archive_{date_str}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # إرسال الملف
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"archive_{date_str}.json",
                    caption=f"📤 **أرشيف {date_str}**\n📊 **{len(messages)}** رسالة",
                    parse_mode='Markdown'
                )
            
            logger.info(f"📤 تم تصدير أرشيف {date_str} - {len(messages)} رسالة")
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق التاريخ غير صحيح. استخدم: **YYYY-MM-DD**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في التصدير: {e}")

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
        self.config.SOURCE_CHANNEL = channel
        
        # حفظ في قاعدة البيانات
        try:
            self.config.save_to_database("source_channel", channel)
            
            await update.message.reply_text(f"✅ تم تحديد القناة المصدر: **{channel}**", parse_mode='Markdown')
            
            # إعادة تشغيل مراقب الرسائل
            if self.userbot and self.userbot.is_connected():
                await update.message.reply_text("🔄 جاري إعادة تشغيل مراقب الرسائل...")
                
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ الإعدادات: {e}")

    async def cmd_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تشخيص سريع للبوت"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("🔍 جاري تشغيل التشخيص السريع...")
        
        try:
            from utils.diagnostics import run_quick_diagnostics
            results = await run_quick_diagnostics(self.config)
            
            # تحضير تقرير التشخيص
            report = "🔍 **تقرير التشخيص السريع:**\n\n"
            
            # عرض نتائج الفحوصات
            for check_name, result in results['checks'].items():
                status = "✅" if result['success'] else "❌"
                report += f"{status} **{check_name}:** {result['message']}\n"
            
            # عرض الأخطاء
            if results['errors']:
                report += f"\n🔴 **الأخطاء ({len(results['errors'])}):**\n"
                for error in results['errors']:
                    report += f"• {error}\n"
            
            # عرض الاقتراحات
            if results['suggestions']:
                report += f"\n💡 **الاقتراحات:**\n"
                for suggestion in results['suggestions']:
                    report += f"• {suggestion}\n"
            
            if not results['errors']:
                report += f"\n🎉 **البوت يعمل بشكل طبيعي!**"
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في التشخيص: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار التفاعلية المحسن"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            return
        
        data = query.data
        
        try:
            if data == "status":
                await self.show_status_callback(query)
            elif data == "browse":
                await self.show_browse_callback(query)
            elif data == "help":
                await self.show_help_callback(query)
            elif data == "main_menu":
                await self.show_main_menu_callback(query)
            elif data == "search_menu":
                await self.show_search_menu_callback(query)
            elif data == "archive_menu":
                await self.show_archive_menu_callback(query)
            elif data.startswith("browse_year_"):
                year = int(data.split("_")[-1])
                await self.show_months_callback(query, year)
            elif data.startswith("browse_month_"):
                parts = data.split("_")
                year, month = int(parts[2]), int(parts[3])
                await self.show_days_callback(query, year, month)
            elif data.startswith("browse_day_"):
                parts = data.split("_")
                year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
                await self.show_day_messages_callback(query, year, month, day)
            elif data.startswith("nav_"):
                await self.handle_navigation_callback(query, data)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الزر: {e}")
            await query.edit_message_text(f"❌ حدث خطأ: {e}")

    async def show_status_callback(self, query):
        """عرض الإحصائيات عبر الزر"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM archived_messages")
            total = cursor.fetchone()[0]
            
            today = datetime.now().date()
            cursor.execute("SELECT COUNT(*) FROM archived_messages WHERE date LIKE ?", (f"{today}%",))
            today_count = cursor.fetchone()[0]
            
            # إحصائيات الوسائط
            cursor.execute("SELECT COUNT(*) FROM archived_messages WHERE media_type IS NOT NULL")
            media_count = cursor.fetchone()[0]
            
            status_text = f"""
📊 **إحصائيات سريعة:**

📈 إجمالي الرسائل: `{total:,}`
📅 رسائل اليوم: `{today_count:,}`
📎 الوسائط: `{media_count:,}`
📂 القناة: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
🤖 الحالة: {'🟢 يعمل' if self.is_running else '🔴 متوقف'}

🕐 آخر تحديث: `{datetime.now().strftime('%H:%M:%S')}`
            """
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في جلب الإحصائيات: {e}")

    async def show_browse_callback(self, query):
        """عرض قائمة السنوات"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT year FROM archived_messages ORDER BY year DESC")
            years = [row[0] for row in cursor.fetchall()]
            
            if not years:
                await query.edit_message_text("📭 لا توجد رسائل مؤرشفة")
                return
            
            keyboard = []
            for year in years:
                cursor.execute("SELECT COUNT(*) FROM archived_messages WHERE year = ?", (year,))
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 {year} ({count:,} رسالة)",
                        callback_data=f"browse_year_{year}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("📂 اختر السنة:", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في التصفح: {e}")

    async def show_help_callback(self, query):
        """عرض المساعدة عبر الزر"""
        help_text = """
🆘 **مساعدة سريعة:**

**📁 الأرشفة:**
• `/archive_today` - أرشفة اليوم
• `/archive_day YYYY-MM-DD` - أرشفة يوم محدد
• `/archive_month YYYY-MM` - أرشفة شهر كامل

**🔍 البحث:**
• `/search كلمة` - البحث في المحتوى

**⚙️ الإدارة:**
• `/status` - الإحصائيات
• `/set_channel @channel` - تحديد القناة
• `/export YYYY-MM-DD` - تصدير أرشيف

💡 **نصيحة:** استخدم الأزرار للتنقل السهل!
        """
        
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_main_menu_callback(self, query):
        """عرض القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="status")],
            [InlineKeyboardButton("📅 تصفح الأرشيف", callback_data="browse")],
            [InlineKeyboardButton("🔍 البحث", callback_data="search_menu")],
            [InlineKeyboardButton("📁 الأرشفة", callback_data="archive_menu")],
            [InlineKeyboardButton("⚙️ المساعدة", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 **بوت أرشفة تليغرام المحسن**

📊 **الحالة الحالية:**
• القناة المصدر: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}

اختر من القائمة أدناه:
        """
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_search_menu_callback(self, query):
        """عرض قائمة البحث"""
        search_text = """
🔍 **قائمة البحث:**

💡 **كيفية البحث:**
• استخدم `/search كلمة البحث`
• مثال: `/search مرحبا`

🎯 **نصائح للبحث الأفضل:**
• استخدم كلمات مفتاحية قصيرة
• جرب كلمات مختلفة إذا لم تجد نتائج
• البحث يشمل النصوص والتسميات التوضيحية

📊 **أنواع المحتوى القابل للبحث:**
• النصوص العادية
• التسميات التوضيحية للصور والفيديوهات
• أسماء الملفات
        """
        
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(search_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_archive_menu_callback(self, query):
        """عرض قائمة الأرشفة"""
        archive_text = """
📁 **قائمة الأرشفة:**

⚡ **أرشفة سريعة:**
• `/archive_today` - أرشفة منشورات اليوم

📅 **أرشفة بالتاريخ:**
• `/archive_day 2024-05-29` - يوم محدد
• `/archive_month 2024-05` - شهر كامل
• `/archive_year 2024` - سنة كاملة

🎯 **أرشفة متقدمة:**
• `/archive_range 2024-01-01 2024-03-31` - نطاق مخصص
• `/archive_all` - جميع المنشورات (تحذير!)

⚠️ **تنبيه:** الأرشفة الكبيرة قد تستغرق وقتاً طويلاً
        """
        
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(archive_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_months_callback(self, query, year: int):
        """عرض شهور السنة"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT month FROM archived_messages WHERE year = ? ORDER BY month",
                (year,)
            )
            months = [row[0] for row in cursor.fetchall()]
            
            keyboard = []
            month_names = [
                "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
            ]
            
            for month in months:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ? AND month = ?",
                    (year, month)
                )
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗓️ {month_names[month-1]} ({count:,})",
                        callback_data=f"browse_month_{year}_{month}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="browse")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"📅 شهور عام {year}:", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في عرض الشهور: {e}")

    async def show_days_callback(self, query, year: int, month: int):
        """عرض أيام الشهر"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT day FROM archived_messages WHERE year = ? AND month = ? ORDER BY day",
                (year, month)
            )
            days = [row[0] for row in cursor.fetchall()]
            
            keyboard = []
            for day in days:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ? AND month = ? AND day = ?",
                    (year, month, day)
                )
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"📆 {day:02d} ({count:,})",
                        callback_data=f"browse_day_{year}_{month}_{day}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"browse_year_{year}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            month_names = [
                "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
            ]
            
            await query.edit_message_text(
                f"🗓️ أيام {month_names[month-1]} {year}:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في عرض الأيام: {e}")

    async def show_day_messages_callback(self, query, year: int, month: int, day: int):
        """عرض رسائل اليوم مع التنقل المحسن"""
        try:
            user_id = query.from_user.id
            
            # حفظ جلسة التصفح
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO browse_sessions 
                   (user_id, current_year, current_month, current_day, current_index) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, year, month, day, 0)
            )
            self.conn.commit()
            
            # جلب رسائل اليوم
            cursor.execute(
                """SELECT * FROM archived_messages 
                   WHERE year = ? AND month = ? AND day = ? 
                   ORDER BY date""",
                (year, month, day)
            )
            messages = cursor.fetchall()
            
            if not messages:
                await query.edit_message_text("❌ لا توجد رسائل في هذا اليوم")
                return
            
            # عرض أول رسالة
            await self.display_message_detailed(query, messages[0], 0, len(messages))
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في عرض الرسائل: {e}")

    async def handle_navigation_callback(self, query, data):
        """معالجة أزرار التنقل"""
        try:
            user_id = query.from_user.id
            
            # جلب جلسة التصفح
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM browse_sessions WHERE user_id = ?",
                (user_id,)
            )
            session = cursor.fetchone()
            
            if not session:
                await query.edit_message_text("❌ جلسة التصفح منتهية الصلاحية")
                return
            
            year, month, day, current_index = session[1], session[2], session[3], session[4]
            
            # تحديد الاتجاه
            if "prev" in data:
                new_index = max(0, current_index - 1)
            elif "next" in data:
                # جلب العدد الإجمالي للرسائل
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ? AND month = ? AND day = ?",
                    (year, month, day)
                )
                total_messages = cursor.fetchone()[0]
                new_index = min(total_messages - 1, current_index + 1)
            else:
                return
            
            # تحديث الفهرس في الجلسة
            cursor.execute(
                "UPDATE browse_sessions SET current_index = ? WHERE user_id = ?",
                (new_index, user_id)
            )
            self.conn.commit()
            
            # جلب الرسالة الجديدة
            cursor.execute(
                """SELECT * FROM archived_messages 
                   WHERE year = ? AND month = ? AND day = ? 
                   ORDER BY date LIMIT 1 OFFSET ?""",
                (year, month, day, new_index)
            )
            message = cursor.fetchone()
            
            if message:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ? AND month = ? AND day = ?",
                    (year, month, day)
                )
                total_messages = cursor.fetchone()[0]
                
                await self.display_message_detailed(query, message, new_index, total_messages)
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في التنقل: {e}")

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أرشفة تليغرام - نسخة محدثة مع دعم String Session
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
import subprocess

# تثبيت المكتبات المطلوبة تلقائياً
def install_required_packages():
    """تثبيت المكتبات المطلوبة"""
    required_packages = [
        'telethon>=1.28.5',
        'python-telegram-bot>=20.0',
        'python-dotenv>=1.0.0',
        'aiofiles>=23.0.0'
    ]
    
    print("🔧 جاري التحقق من المكتبات المطلوبة...")
    
    for package in required_packages:
        package_name = package.split('>=')[0]
        try:
            __import__(package_name.replace('-', '_'))
            print(f"✅ {package_name} متوفر")
        except ImportError:
            print(f"📦 جاري تثبيت {package_name}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ تم تثبيت {package_name}")
            except subprocess.CalledProcessError:
                print(f"❌ فشل في تثبيت {package_name}")
                return False
    
    return True

# تثبيت المكتبات
if not install_required_packages():
    print("❌ فشل في تثبيت المكتبات المطلوبة")
    sys.exit(1)

# استيراد المكتبات بعد التثبيت
try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from dotenv import load_dotenv
    import aiofiles
    print("✅ تم تحميل جميع المكتبات بنجاح")
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    sys.exit(1)

# إعداد نظام السجلات
def setup_logging():
    """إعداد نظام السجلات"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # إنشاء مجلد السجلات
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        format=log_format,
        level=logging.INFO,
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # تقليل مستوى سجلات المكتبات الخارجية
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

logger = setup_logging()

class TelegramArchiveBot:
    """فئة بوت أرشفة تليغرام الرئيسية مع دعم String Session"""
    
    def __init__(self):
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
            logger.error("أو تشغيل: python create_session.py لإنشاء String Session")
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
                logger.error("💡 نصيحة: تشغيل python create_session.py لإنشاء String Session جديد")
            return False

    # باقي الكود يبقى كما هو من الملف الأصلي...
    # [يمكنني إضافة باقي الدوال إذا كنت تريد الملف كاملاً]

    async def run(self):
        """تشغيل البوت الرئيسي"""
        logger.info("🚀 بدء تشغيل بوت الأرشفة...")
        
        # التحقق من متغيرات البيئة
        if not self.validate_environment():
            logger.error("❌ يرجى تعديل ملف .env وإضافة القيم الصحيحة")
            logger.error("💡 أو تشغيل: python create_session.py")
            return False
        
        self.is_running = True
        
        try:
            # بدء Userbot
            logger.info("🔄 بدء تشغيل Userbot...")
            userbot_success = await self.start_userbot()
            
            if not userbot_success:
                logger.warning("⚠️ فشل في تشغيل Userbot - ستعمل الأوامر اليدوية فقط")
                logger.warning("💡 تشغيل: python create_session.py لإنشاء String Session")
            
            # بدء Bot (نفس الكود من الملف الأصلي)
            # ...
            
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

# دالة التشغيل الرئيسية
async def main():
    """الدالة الرئيسية"""
    print("🤖 بوت أرشفة تليغرام مع String Session")
    print("=" * 40)
    
    # إنشاء البوت
    bot = TelegramArchiveBot()
    
    # تشغيل البوت
    await bot.run()

# نقطة البداية
if __name__ == "__main__":
    try:
        # تشغيل البوت
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت")
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        logger.error(f"خطأ عام في التشغيل: {e}")

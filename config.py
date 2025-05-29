#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف إعدادات بوت أرشفة تليغرام
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """فئة إعدادات البوت"""
    
    def __init__(self):
        """تهيئة الإعدادات"""
        # تحميل متغيرات البيئة
        self._load_environment()
        
        # إعدادات Telethon (Userbot)
        self.API_ID = os.getenv('API_ID')
        self.API_HASH = os.getenv('API_HASH')
        self.PHONE_NUMBER = os.getenv('PHONE_NUMBER')
        self.STRING_SESSION = os.getenv('STRING_SESSION')
        
        # إعدادات Bot Token
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        # إعدادات القناة والمدراء
        self.SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        self.ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]
        
        # إعدادات إضافية
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        
        # تحميل الإعدادات من قاعدة البيانات
        self._load_from_database()
    
    def _load_environment(self):
        """تحميل متغيرات البيئة"""
        # إنشاء ملف .env إذا لم يكن موجوداً
        env_file = Path('.env')
        if not env_file.exists():
            self._create_env_file()
        
        # تحميل متغيرات البيئة
        load_dotenv()
    
    def _create_env_file(self):
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
        
        logging.warning("📝 تم إنشاء ملف .env - يرجى تعديل القيم قبل التشغيل")
    
    def _load_from_database(self):
        """تحميل الإعدادات من قاعدة البيانات"""
        try:
            # التحقق من وجود قاعدة البيانات
            db_file = Path('archive.db')
            if not db_file.exists():
                return
            
            import sqlite3
            conn = sqlite3.connect('archive.db')
            cursor = conn.cursor()
            
            # التحقق من وجود جدول الإعدادات
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not cursor.fetchone():
                return
            
            # تحميل الإعدادات
            cursor.execute("SELECT key, value FROM settings")
            settings = cursor.fetchall()
            
            for key, value in settings:
                if key == 'source_channel' and value:
                    self.SOURCE_CHANNEL = value
            
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الإعدادات من قاعدة البيانات: {e}")
    
    def validate(self):
        """التحقق من صحة الإعدادات"""
        missing_vars = []
        
        if not self.API_ID or self.API_ID == 'your_api_id_here':
            missing_vars.append('API_ID')
        
        if not self.API_HASH or self.API_HASH == 'your_api_hash_here':
            missing_vars.append('API_HASH')
        
        if not self.BOT_TOKEN or self.BOT_TOKEN == 'your_bot_token_here':
            missing_vars.append('BOT_TOKEN')
        
        # التحقق من وجود String Session أو رقم الهاتف
        if not self.STRING_SESSION or self.STRING_SESSION == 'your_string_session_here':
            if not self.PHONE_NUMBER or self.PHONE_NUMBER == '+1234567890':
                missing_vars.append('STRING_SESSION أو PHONE_NUMBER')
        
        if not self.ADMIN_IDS:
            missing_vars.append('ADMIN_IDS')
        
        if missing_vars:
            logging.error(f"❌ متغيرات البيئة المفقودة: {', '.join(missing_vars)}")
            logging.error("يرجى تعديل ملف .env وإضافة القيم الصحيحة")
            return False
        
        return True
    
    def save_to_database(self, key, value):
        """حفظ إعداد في قاعدة البيانات"""
        try:
            import sqlite3
            conn = sqlite3.connect('archive.db')
            cursor = conn.cursor()
            
            # التحقق من وجود جدول الإعدادات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # حفظ الإعداد
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ الإعداد في قاعدة البيانات: {e}")
            return False

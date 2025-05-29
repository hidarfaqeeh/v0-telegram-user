#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف إعدادات بوت أرشفة تليغرام مع دعم قواعد البيانات المختلفة
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

class DatabaseConfig:
    """فئة إعدادات قاعدة البيانات"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///archive.db')
        self.parsed_url = urlparse(self.database_url)
        
        # تحديد نوع قاعدة البيانات
        self.db_type = self.parsed_url.scheme.lower()
        
        # إعدادات الاتصال
        self.host = self.parsed_url.hostname
        self.port = self.parsed_url.port
        self.username = self.parsed_url.username
        self.password = self.parsed_url.password
        self.database = self.parsed_url.path.lstrip('/')
        
        # إعدادات خاصة بكل نوع
        self._setup_db_specific_config()
    
    def _setup_db_specific_config(self):
        """إعداد خاص بنوع قاعدة البيانات"""
        if self.db_type == 'sqlite':
            self.db_file = self.database_url.replace('sqlite:///', '')
            self.connection_string = self.db_file
        
        elif self.db_type == 'postgresql':
            self.port = self.port or 5432
            self.connection_string = {
                'host': self.host,
                'port': self.port,
                'user': self.username,
                'password': self.password,
                'database': self.database
            }
        
        elif self.db_type == 'mysql':
            self.port = self.port or 3306
            self.connection_string = {
                'host': self.host,
                'port': self.port,
                'user': self.username,
                'password': self.password,
                'database': self.database
            }
    
    def get_connection_params(self):
        """الحصول على معاملات الاتصال"""
        return {
            'db_type': self.db_type,
            'connection_string': self.connection_string,
            'database_url': self.database_url
        }

class Config:
    """فئة إعدادات البوت المحدثة"""
    
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
        
        # إعدادات قاعدة البيانات
        self.database = DatabaseConfig()
        
        # إعدادات إضافية
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    def _load_environment(self):
        """تحميل متغيرات البيئة"""
        env_file = Path('.env')
        if not env_file.exists():
            self._create_env_file()
        
        load_dotenv()
    
    def _create_env_file(self):
        """إنشاء ملف .env تجريبي"""
        env_content = """# إعدادات Telethon (Userbot)
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890
STRING_SESSION=your_string_session_here

# إعدادات Bot Token
BOT_TOKEN=your_bot_token_here

# إعدادات القناة والمدراء
SOURCE_CHANNEL=@your_channel_username
ADMIN_IDS=123456789,987654321

# إعدادات قاعدة البيانات
DATABASE_URL=sqlite:///archive.db

# إعدادات إضافية
DEBUG=false
ENVIRONMENT=development
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logging.warning("📝 تم إنشاء ملف .env - يرجى تعديل القيم قبل التشغيل")
    
    def validate(self):
        """التحقق من صحة الإعدادات"""
        missing_vars = []
        
        if not self.API_ID or self.API_ID == 'your_api_id_here':
            missing_vars.append('API_ID')
        
        if not self.API_HASH or self.API_HASH == 'your_api_hash_here':
            missing_vars.append('API_HASH')
        
        if not self.BOT_TOKEN or self.BOT_TOKEN == 'your_bot_token_here':
            missing_vars.append('BOT_TOKEN')
        
        if not self.STRING_SESSION or self.STRING_SESSION == 'your_string_session_here':
            if not self.PHONE_NUMBER or self.PHONE_NUMBER == '+1234567890':
                missing_vars.append('STRING_SESSION أو PHONE_NUMBER')
        
        if not self.ADMIN_IDS:
            missing_vars.append('ADMIN_IDS')
        
        if missing_vars:
            logging.error(f"❌ متغيرات البيئة المفقودة: {', '.join(missing_vars)}")
            return False
        
        return True

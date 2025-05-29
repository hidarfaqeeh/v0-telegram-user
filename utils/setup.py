#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات إعداد البيئة والمتطلبات
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """التحقق من المتطلبات المطلوبة"""
    print("🔧 جاري التحقق من المتطلبات...")
    
    required_packages = [
        'telethon>=1.28.5',
        'python-telegram-bot>=20.0',
        'python-dotenv>=1.0.0',
        'aiofiles>=23.0.0',
        'requests>=2.25.0'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        package_name = package.split('>=')[0]
        try:
            __import__(package_name.replace('-', '_'))
            print(f"✅ {package_name} متوفر")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package_name} غير متوفر")
    
    if missing_packages:
        print(f"\n📦 جاري تثبيت {len(missing_packages)} مكتبة...")
        install_packages(missing_packages)
    else:
        print("✅ جميع المتطلبات متوفرة")
    
    return True

def install_packages(packages):
    """تثبيت المكتبات المطلوبة"""
    for package in packages:
        package_name = package.split('>=')[0]
        print(f"📦 جاري تثبيت {package_name}...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ تم تثبيت {package_name}")
        except subprocess.CalledProcessError:
            print(f"❌ فشل في تثبيت {package_name}")
            print(f"💡 جرب: pip install {package}")

def setup_environment():
    """إعداد البيئة الكاملة"""
    print("🔧 بدء إعداد البيئة...")
    
    # إنشاء المجلدات المطلوبة
    create_directories()
    
    # إنشاء ملف .env إذا لم يكن موجوداً
    create_env_file()
    
    # تثبيت المتطلبات
    check_requirements()
    
    # إنشاء ملفات إضافية
    create_additional_files()
    
    print("\n✅ تم إعداد البيئة بنجاح!")
    print("\n📋 الخطوات التالية:")
    print("1. عدل ملف .env وأضف البيانات الصحيحة")
    print("2. شغل: python run.py --session لإنشاء String Session")
    print("3. شغل: python run.py لتشغيل البوت")

def create_directories():
    """إنشاء المجلدات المطلوبة"""
    directories = [
        'archive', 'exports', 'backups', 'logs', 
        'config', 'sessions', 'src', 'utils'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 تم إنشاء مجلد: {directory}")

def create_env_file():
    """إنشاء ملف .env إذا لم يكن موجوداً"""
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ ملف .env موجود بالفعل")
        return
    
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
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("📝 تم إنشاء ملف .env")

def create_additional_files():
    """إنشاء ملفات إضافية"""
    
    # إنشاء __init__.py للمجلدات
    init_files = ['src/__init__.py', 'utils/__init__.py']
    
    for init_file in init_files:
        Path(init_file).touch()
    
    # إنشاء .gitignore
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Environment variables
.env
.env.local
.env.development
.env.test
.env.production

# Database files
*.db
*.sqlite
*.sqlite3

# Session files
*.session
sessions/

# Log files
*.log
logs/

# Archive and export files
archive/
exports/
backups/

# Virtual environments
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("📝 تم إنشاء ملف .gitignore")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة تشخيص مشاكل بوت تليغرام
تساعد في اكتشاف وحل مشاكل عدم استجابة البوت
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
import subprocess
import json
import sqlite3
from datetime import datetime

# تثبيت المكتبات المطلوبة
def install_required_packages():
    """تثبيت المكتبات المطلوبة للتشخيص"""
    required_packages = [
        'python-telegram-bot>=20.0',
        'python-dotenv>=1.0.0',
        'requests>=2.25.0'
    ]
    
    print("🔧 جاري التحقق من المكتبات...")
    
    for package in required_packages:
        package_name = package.split('>=')[0]
        try:
            __import__(package_name.replace('-', '_'))
        except ImportError:
            print(f"📦 جاري تثبيت {package_name}...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return True

install_required_packages()

try:
    from telegram import Bot, Update
    from telegram.ext import Application
    from dotenv import load_dotenv
    import requests
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    sys.exit(1)

class BotDiagnostics:
    """فئة تشخيص مشاكل البوت"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def print_header(self):
        """طباعة رأس التشخيص"""
        print("=" * 70)
        print("🔍 أداة تشخيص بوت أرشفة تليغرام")
        print("=" * 70)
        print()
    
    def print_section(self, title):
        """طباعة عنوان قسم"""
        print(f"\n📋 {title}")
        print("-" * 50)
    
    def check_environment_file(self):
        """التحقق من ملف البيئة"""
        self.print_section("فحص ملف البيئة (.env)")
        
        env_file = Path('.env')
        if not env_file.exists():
            self.errors.append("ملف .env غير موجود")
            print("❌ ملف .env غير موجود")
            print("💡 قم بإنشاء ملف .env من .env.example")
            return False
        
        print("✅ ملف .env موجود")
        
        # تحميل متغيرات البيئة
        load_dotenv()
        
        required_vars = {
            'BOT_TOKEN': 'رمز البوت',
            'API_ID': 'معرف API',
            'API_HASH': 'مفتاح API',
            'ADMIN_IDS': 'معرفات المدراء'
        }
        
        missing_vars = []
        for var, desc in required_vars.items():
            value = os.getenv(var)
            if not value or value in ['your_bot_token_here', 'your_api_id_here', 'your_api_hash_here', '123456789,987654321']:
                missing_vars.append(f"{var} ({desc})")
                print(f"❌ {var} غير مُعرّف أو يحتوي على قيمة افتراضية")
            else:
                if var == 'BOT_TOKEN':
                    masked = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
                    print(f"✅ {var}: {masked}")
                elif var in ['API_ID', 'ADMIN_IDS']:
                    print(f"✅ {var}: {value}")
                else:
                    print(f"✅ {var}: {value[:8]}...")
        
        if missing_vars:
            self.errors.extend(missing_vars)
            return False
        
        return True
    
    async def test_bot_token(self):
        """اختبار صحة رمز البوت"""
        self.print_section("اختبار رمز البوت")
        
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("❌ رمز البوت غير موجود")
            return False
        
        try:
            bot = Bot(token=bot_token)
            me = await bot.get_me()
            
            print(f"✅ البوت متصل بنجاح!")
            print(f"🤖 اسم البوت: {me.first_name}")
            print(f"📧 معرف البوت: @{me.username}")
            print(f"🆔 ID البوت: {me.id}")
            print(f"🔒 يمكنه الانضمام للمجموعات: {me.can_join_groups}")
            print(f"📨 يمكنه قراءة جميع الرسائل: {me.can_read_all_group_messages}")
            
            self.results['bot_info'] = {
                'name': me.first_name,
                'username': me.username,
                'id': me.id,
                'can_join_groups': me.can_join_groups,
                'can_read_all_group_messages': me.can_read_all_group_messages
            }
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في الاتصال بالبوت: {e}")
            self.errors.append(f"خطأ في رمز البوت: {e}")
            
            # نصائح حل المشكلة
            if "Unauthorized" in str(e):
                print("💡 رمز البوت غير صحيح أو منتهي الصلاحية")
                print("   - تأكد من نسخ الرمز من @BotFather بالكامل")
                print("   - تأكد من عدم وجود مسافات إضافية")
            elif "Network" in str(e) or "timeout" in str(e).lower():
                print("💡 مشكلة في الاتصال بالإنترنت")
                print("   - تأكد من اتصالك بالإنترنت")
                print("   - قد تحتاج لاستخدام VPN")
            
            return False
    
    def check_admin_ids(self):
        """التحقق من معرفات المدراء"""
        self.print_section("فحص معرفات المدراء")
        
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if not admin_ids_str:
            print("❌ ADMIN_IDS غير محدد")
            self.errors.append("ADMIN_IDS مطلوب")
            return False
        
        try:
            admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]
            
            if not admin_ids:
                print("❌ لا توجد معرفات صحيحة في ADMIN_IDS")
                self.errors.append("معرفات المدراء غير صحيحة")
                return False
            
            print(f"✅ تم العثور على {len(admin_ids)} مدير:")
            for i, admin_id in enumerate(admin_ids, 1):
                print(f"   {i}. {admin_id}")
            
            self.results['admin_ids'] = admin_ids
            return True
            
        except Exception as e:
            print(f"❌ خطأ في معالجة ADMIN_IDS: {e}")
            self.errors.append(f"خطأ في ADMIN_IDS: {e}")
            return False
    
    async def test_bot_commands(self):
        """اختبار أوامر البوت"""
        self.print_section("اختبار أوامر البوت")
        
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("❌ رمز البوت غير موجود")
            return False
        
        try:
            bot = Bot(token=bot_token)
            
            # الحصول على قائمة الأوامر
            commands = await bot.get_my_commands()
            
            if commands:
                print(f"✅ البوت لديه {len(commands)} أمر مُعرّف:")
                for cmd in commands:
                    print(f"   /{cmd.command} - {cmd.description}")
            else:
                print("⚠️ البوت ليس لديه أوامر مُعرّفة")
                self.warnings.append("لا توجد أوامر معرفة للبوت")
            
            # اختبار إرسال رسالة (إذا كان هناك مدراء)
            admin_ids = self.results.get('admin_ids', [])
            if admin_ids:
                test_admin = admin_ids[0]
                try:
                    test_message = f"🔍 اختبار البوت - {datetime.now().strftime('%H:%M:%S')}"
                    await bot.send_message(chat_id=test_admin, text=test_message)
                    print(f"✅ تم إرسال رسالة اختبار للمدير {test_admin}")
                    return True
                except Exception as e:
                    print(f"❌ فشل في إرسال رسالة للمدير {test_admin}: {e}")
                    if "Forbidden" in str(e):
                        print("💡 المدير لم يبدأ محادثة مع البوت بعد")
                        print("   - يجب على المدير إرسال /start للبوت أولاً")
                    self.errors.append(f"لا يمكن إرسال رسالة للمدير: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في اختبار أوامر البوت: {e}")
            self.errors.append(f"خطأ في أوامر البوت: {e}")
            return False
    
    def check_database(self):
        """فحص قاعدة البيانات"""
        self.print_section("فحص قاعدة البيانات")
        
        try:
            db_file = Path('archive.db')
            
            if not db_file.exists():
                print("⚠️ قاعدة البيانات غير موجودة (ستُنشأ عند التشغيل)")
                return True
            
            # فحص قاعدة البيانات
            conn = sqlite3.connect('archive.db')
            cursor = conn.cursor()
            
            # فحص الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            expected_tables = ['archived_messages', 'settings', 'admins']
            existing_tables = [table[0] for table in tables]
            
            print(f"✅ قاعدة البيانات موجودة ({db_file.stat().st_size / 1024:.2f} KB)")
            
            for table in expected_tables:
                if table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ جدول {table}: {count} سجل")
                else:
                    print(f"   ⚠️ جدول {table} غير موجود")
                    self.warnings.append(f"جدول {table} غير موجود")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
            self.errors.append(f"خطأ في قاعدة البيانات: {e}")
            return False
    
    def check_directories(self):
        """فحص المجلدات المطلوبة"""
        self.print_section("فحص المجلدات")
        
        required_dirs = ['archive', 'exports', 'backups', 'logs', 'config', 'sessions']
        
        for directory in required_dirs:
            dir_path = Path(directory)
            if dir_path.exists():
                files_count = len(list(dir_path.glob('*')))
                print(f"✅ مجلد {directory}: {files_count} ملف")
            else:
                print(f"⚠️ مجلد {directory} غير موجود (سيُنشأ تلقائياً)")
        
        return True
    
    def check_log_files(self):
        """فحص ملفات السجل"""
        self.print_section("فحص ملفات السجل")
        
        log_file = Path('logs/bot.log')
        
        if not log_file.exists():
            print("⚠️ ملف السجل غير موجود")
            print("💡 هذا طبيعي إذا لم يتم تشغيل البوت من قبل")
            return True
        
        try:
            # قراءة آخر 10 أسطر من السجل
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"✅ ملف السجل موجود ({len(lines)} سطر)")
            
            if lines:
                print("📋 آخر 5 إدخالات في السجل:")
                for line in lines[-5:]:
                    line = line.strip()
                    if line:
                        # تحديد مستوى السجل
                        if "ERROR" in line:
                            print(f"   ❌ {line}")
                        elif "WARNING" in line:
                            print(f"   ⚠️ {line}")
                        elif "INFO" in line:
                            print(f"   ℹ️ {line}")
                        else:
                            print(f"   📝 {line}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في قراءة ملف السجل: {e}")
            return False
    
    def check_network_connectivity(self):
        """فحص الاتصال بالشبكة"""
        self.print_section("فحص الاتصال بالشبكة")
        
        test_urls = [
            ("api.telegram.org", "Telegram API"),
            ("google.com", "الإنترنت العام"),
        ]
        
        for url, desc in test_urls:
            try:
                response = requests.get(f"https://{url}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ الاتصال بـ {desc} يعمل")
                else:
                    print(f"⚠️ مشكلة في الاتصال بـ {desc} (كود: {response.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"❌ فشل الاتصال بـ {desc}: {e}")
                if "telegram" in url:
                    self.errors.append(f"لا يمكن الوصول إلى {desc}")
                    print("💡 قد تحتاج لاستخدام VPN أو proxy")
        
        return True
    
    def generate_fixes(self):
        """إنتاج اقتراحات لحل المشاكل"""
        self.print_section("اقتراحات الحلول")
        
        if not self.errors and not self.warnings:
            print("🎉 لم يتم العثور على مشاكل!")
            print("✅ البوت يجب أن يعمل بشكل طبيعي")
            return
        
        if self.errors:
            print("🔴 مشاكل يجب حلها:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        if self.warnings:
            print("\n🟡 تحذيرات (اختيارية):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        print("\n💡 خطوات الحل المقترحة:")
        
        # حلول محددة حسب نوع المشكلة
        if any("رمز البوت" in error for error in self.errors):
            print("🔧 مشكلة رمز البوت:")
            print("   1. اذهب إلى @BotFather في تليغرام")
            print("   2. أرسل /mybots")
            print("   3. اختر البوت الخاص بك")
            print("   4. اضغط 'API Token'")
            print("   5. انسخ الرمز كاملاً إلى ملف .env")
        
        if any("ADMIN_IDS" in error for error in self.errors):
            print("\n🔧 مشكلة معرفات المدراء:")
            print("   1. أرسل رسالة لـ @userinfobot في تليغرام")
            print("   2. انسخ رقم User ID")
            print("   3. أضفه إلى ADMIN_IDS في ملف .env")
            print("   4. مثال: ADMIN_IDS=123456789,987654321")
        
        if any("لا يمكن إرسال رسالة" in error for error in self.errors):
            print("\n🔧 مشكلة إرسال الرسائل:")
            print("   1. ابحث عن البوت في تليغرام باستخدام معرفه")
            print("   2. اضغط 'Start' أو أرسل /start")
            print("   3. جرب إرسال أوامر أخرى مثل /help")
        
        if any("الاتصال" in error for error in self.errors):
            print("\n🔧 مشكلة الاتصال:")
            print("   1. تأكد من اتصالك بالإنترنت")
            print("   2. جرب استخدام VPN")
            print("   3. تأكد من عدم حظر تليغرام في منطقتك")
    
    async def run_full_diagnosis(self):
        """تشغيل التشخيص الكامل"""
        self.print_header()
        
        print("🔍 بدء التشخيص الشامل للبوت...")
        print("⏳ قد يستغرق هذا بضع ثوان...")
        
        # تشغيل جميع الفحوصات
        steps = [
            ("فحص ملف البيئة", self.check_environment_file),
            ("اختبار رمز البوت", self.test_bot_token),
            ("فحص معرفات المدراء", self.check_admin_ids),
            ("اختبار أوامر البوت", self.test_bot_commands),
            ("فحص قاعدة البيانات", self.check_database),
            ("فحص المجلدات", self.check_directories),
            ("فحص ملفات السجل", self.check_log_files),
            ("فحص الاتصال بالشبكة", self.check_network_connectivity),
        ]
        
        results = {}
        for step_name, step_func in steps:
            try:
                if asyncio.iscoroutinefunction(step_func):
                    result = await step_func()
                else:
                    result = step_func()
                results[step_name] = result
            except Exception as e:
                print(f"❌ خطأ في {step_name}: {e}")
                results[step_name] = False
                self.errors.append(f"خطأ في {step_name}: {e}")
        
        # إنتاج التقرير النهائي
        self.generate_fixes()
        
        # حفظ تقرير التشخيص
        await self.save_diagnosis_report(results)
    
    async def save_diagnosis_report(self, results):
        """حفظ تقرير التشخيص"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'errors': self.errors,
                'warnings': self.warnings,
                'bot_info': self.results.get('bot_info', {}),
                'admin_ids': self.results.get('admin_ids', [])
            }
            
            report_file = Path('bot_diagnosis_report.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 تم حفظ تقرير التشخيص في: {report_file}")
            
        except Exception as e:
            print(f"⚠️ لم يتم حفظ التقرير: {e}")

async def main():
    """الدالة الرئيسية"""
    diagnostics = BotDiagnostics()
    await diagnostics.run_full_diagnosis()
    
    print("\n" + "=" * 70)
    print("🏁 انتهى التشخيص")
    
    if diagnostics.errors:
        print("❌ يرجى حل المشاكل المذكورة أعلاه قبل تشغيل البوت")
        return False
    else:
        print("✅ البوت جاهز للتشغيل!")
        return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if not result:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ تم إلغاء التشخيص")
    except Exception as e:
        print(f"\n❌ خطأ في التشخيص: {e}")
        sys.exit(1)

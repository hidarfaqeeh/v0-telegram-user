#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات تشخيص مشاكل البوت
"""

import asyncio
import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

try:
    from telegram import Bot
    import requests
except ImportError:
    print("❌ المكتبات المطلوبة غير مثبتة")
    print("🔧 قم بتشغيل: python run.py --setup")
    sys.exit(1)

async def run_diagnostics():
    """تشغيل التشخيص الكامل"""
    print("🔍 بدء التشخيص الشامل للبوت...")
    print("⏳ قد يستغرق هذا بضع ثوان...")
    
    results = {
        'checks': {},
        'errors': [],
        'warnings': [],
        'suggestions': []
    }
    
    # تشغيل جميع الفحوصات
    checks = [
        ("فحص ملف البيئة", check_environment_file),
        ("اختبار رمز البوت", test_bot_token),
        ("فحص معرفات المدراء", check_admin_ids),
        ("فحص قاعدة البيانات", check_database),
        ("فحص المجلدات", check_directories),
        ("فحص الاتصال بالشبكة", check_network_connectivity),
    ]
    
    for check_name, check_func in checks:
        try:
            print(f"\n📋 {check_name}...")
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            results['checks'][check_name] = result
            
            if result['success']:
                print(f"✅ {result['message']}")
            else:
                print(f"❌ {result['message']}")
                results['errors'].append(f"{check_name}: {result['message']}")
                
        except Exception as e:
            error_msg = f"خطأ في {check_name}: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
            results['checks'][check_name] = {
                'success': False,
                'message': str(e)
            }
    
    # إنتاج الاقتراحات
    generate_suggestions(results)
    
    # حفظ تقرير التشخيص
    await save_diagnosis_report(results)
    
    # طباعة الملخص النهائي
    print_final_summary(results)
    
    return results

async def run_quick_diagnostics(config):
    """تشخيص سريع للبوت"""
    results = {
        'checks': {},
        'errors': [],
        'warnings': [],
        'suggestions': []
    }
    
    # فحص سريع للإعدادات
    if config.validate():
        results['checks']['الإعدادات'] = {
            'success': True,
            'message': 'جميع الإعدادات صحيحة'
        }
    else:
        results['checks']['الإعدادات'] = {
            'success': False,
            'message': 'إعدادات مفقودة أو غير صحيحة'
        }
        results['errors'].append('إعدادات مفقودة')
    
    # فحص سريع لرمز البوت
    if config.BOT_TOKEN and config.BOT_TOKEN != 'your_bot_token_here':
        try:
            bot = Bot(token=config.BOT_TOKEN)
            me = await bot.get_me()
            results['checks']['رمز البوت'] = {
                'success': True,
                'message': f'البوت متصل: {me.first_name}'
            }
        except Exception as e:
            results['checks']['رمز البوت'] = {
                'success': False,
                'message': f'خطأ في رمز البوت: {e}'
            }
            results['errors'].append('رمز البوت غير صحيح')
    else:
        results['checks']['رمز البوت'] = {
            'success': False,
            'message': 'رمز البوت غير محدد'
        }
        results['errors'].append('رمز البوت مطلوب')
    
    # إضافة اقتراحات سريعة
    if results['errors']:
        results['suggestions'].append('شغل python run.py --diagnostics للتشخيص المفصل')
        results['suggestions'].append('تحقق من ملف .env')
    
    return results

def check_environment_file():
    """فحص ملف البيئة"""
    env_file = Path('.env')
    
    if not env_file.exists():
        return {
            'success': False,
            'message': 'ملف .env غير موجود'
        }
    
    # تحميل متغيرات البيئة
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'ADMIN_IDS']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value in ['your_bot_token_here', 'your_api_id_here', 'your_api_hash_here', '123456789,987654321']:
            missing_vars.append(var)
    
    if missing_vars:
        return {
            'success': False,
            'message': f'متغيرات مفقودة: {", ".join(missing_vars)}'
        }
    
    return {
        'success': True,
        'message': 'ملف .env صحيح ومكتمل'
    }

async def test_bot_token():
    """اختبار رمز البوت"""
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token or bot_token == 'your_bot_token_here':
        return {
            'success': False,
            'message': 'رمز البوت غير محدد'
        }
    
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        
        return {
            'success': True,
            'message': f'البوت متصل: {me.first_name} (@{me.username})'
        }
        
    except Exception as e:
        error_msg = str(e)
        if "Unauthorized" in error_msg:
            suggestion = "رمز البوت غير صحيح - تحقق من @BotFather"
        elif "Network" in error_msg:
            suggestion = "مشكلة في الاتصال - تحقق من الإنترنت"
        else:
            suggestion = "خطأ غير معروف"
        
        return {
            'success': False,
            'message': f'{suggestion}: {error_msg}'
        }

def check_admin_ids():
    """فحص معرفات المدراء"""
    admin_ids_str = os.getenv('ADMIN_IDS', '')
    
    if not admin_ids_str or admin_ids_str == '123456789,987654321':
        return {
            'success': False,
            'message': 'معرفات المدراء غير محددة'
        }
    
    try:
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]
        
        if not admin_ids:
            return {
                'success': False,
                'message': 'لا توجد معرفات صحيحة'
            }
        
        return {
            'success': True,
            'message': f'تم العثور على {len(admin_ids)} مدير'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'خطأ في معالجة معرفات المدراء: {e}'
        }

def check_database():
    """فحص قاعدة البيانات"""
    db_file = Path('archive.db')
    
    if not db_file.exists():
        return {
            'success': True,
            'message': 'قاعدة البيانات ستُنشأ عند التشغيل'
        }
    
    try:
        conn = sqlite3.connect('archive.db')
        cursor = conn.cursor()
        
        # فحص الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        expected_tables = ['archived_messages', 'settings', 'admins']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            conn.close()
            return {
                'success': False,
                'message': f'جداول مفقودة: {", ".join(missing_tables)}'
            }
        
        # فحص عدد الرسائل
        cursor.execute("SELECT COUNT(*) FROM archived_messages")
        message_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'message': f'قاعدة البيانات صحيحة ({message_count:,} رسالة)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'خطأ في قاعدة البيانات: {e}'
        }

def check_directories():
    """فحص المجلدات المطلوبة"""
    required_dirs = ['archive', 'exports', 'backups', 'logs', 'config', 'sessions']
    missing_dirs = []
    
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    if missing_dirs:
        return {
            'success': False,
            'message': f'مجلدات مفقودة: {", ".join(missing_dirs)}'
        }
    
    return {
        'success': True,
        'message': 'جميع المجلدات موجودة'
    }

def check_network_connectivity():
    """فحص الاتصال بالشبكة"""
    test_urls = [
        ("api.telegram.org", "Telegram API"),
        ("google.com", "الإنترنت العام"),
    ]
    
    failed_connections = []
    
    for url, desc in test_urls:
        try:
            response = requests.get(f"https://{url}", timeout=10)
            if response.status_code != 200:
                failed_connections.append(desc)
        except requests.exceptions.RequestException:
            failed_connections.append(desc)
    
    if failed_connections:
        return {
            'success': False,
            'message': f'فشل الاتصال بـ: {", ".join(failed_connections)}'
        }
    
    return {
        'success': True,
        'message': 'الاتصال بالشبكة يعمل بشكل طبيعي'
    }

def generate_suggestions(results):
    """إنتاج اقتراحات لحل المشاكل"""
    suggestions = []
    
    # اقتراحات حسب نوع المشكلة
    for error in results['errors']:
        if "ملف .env" in error:
            suggestions.append("شغل python run.py --setup لإنشاء ملف .env")
        elif "رمز البوت" in error:
            suggestions.append("احصل على رمز جديد من @BotFather")
        elif "معرفات المدراء" in error:
            suggestions.append("أرسل رسالة لـ @userinfobot للحصول على معرفك")
        elif "الاتصال" in error:
            suggestions.append("تحقق من الإنترنت أو استخدم VPN")
        elif "قاعدة البيانات" in error:
            suggestions.append("احذف ملف archive.db ليتم إنشاؤه من جديد")
    
    # إزالة الاقتراحات المكررة
    results['suggestions'] = list(set(suggestions))

async def save_diagnosis_report(results):
    """حفظ تقرير التشخيص"""
    try:
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': str(Path.cwd())
            }
        }
        
        report_file = Path('logs') / f'diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ تقرير التشخيص: {report_file}")
        
    except Exception as e:
        print(f"⚠️ لم يتم حفظ التقرير: {e}")

def print_final_summary(results):
    """طباعة الملخص النهائي"""
    print("\n" + "=" * 60)
    print("📊 ملخص التشخيص")
    print("=" * 60)
    
    total_checks = len(results['checks'])
    successful_checks = sum(1 for check in results['checks'].values() if check['success'])
    
    print(f"✅ الفحوصات الناجحة: {successful_checks}/{total_checks}")
    print(f"❌ الأخطاء: {len(results['errors'])}")
    print(f"⚠️ التحذيرات: {len(results['warnings'])}")
    
    if results['errors']:
        print(f"\n🔴 يجب حل {len(results['errors'])} مشكلة قبل تشغيل البوت")
        for suggestion in results['suggestions']:
            print(f"💡 {suggestion}")
    else:
        print("\n🎉 البوت جاهز للتشغيل!")
        print("🚀 شغل: python run.py")
    
    print("=" * 60)

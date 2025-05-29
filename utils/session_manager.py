#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير جلسات تليغرام وإنشاء String Session
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from dotenv import load_dotenv
except ImportError:
    print("❌ المكتبات المطلوبة غير مثبتة")
    print("🔧 قم بتشغيل: python run.py --setup")
    sys.exit(1)

async def create_string_session():
    """إنشاء String Session جديد"""
    print("🔐 مولد String Session لبوت أرشفة تليغرام")
    print("=" * 50)
    
    # الحصول على بيانات API
    api_id, api_hash = get_api_credentials()
    
    # الحصول على رقم الهاتف
    phone = get_phone_number()
    
    print("\n🔄 جاري إنشاء String Session...")
    print("⏳ قد تستغرق هذه العملية بضع دقائق...")
    
    try:
        # إنشاء عميل Telethon مع StringSession
        client = TelegramClient(StringSession(), api_id, api_hash)
        
        print("\n📡 جاري الاتصال بـ Telegram...")
        await client.start(phone=phone)
        
        # التحقق من نجاح الاتصال
        me = await client.get_me()
        print(f"\n✅ تم تسجيل الدخول بنجاح!")
        print(f"👤 الاسم: {me.first_name} {me.last_name or ''}")
        print(f"📱 المعرف: @{me.username or 'غير محدد'}")
        print(f"🆔 ID: {me.id}")
        
        # الحصول على String Session
        string_session = client.session.save()
        
        print("\n" + "=" * 50)
        print("🎉 تم إنشاء String Session بنجاح!")
        print("=" * 50)
        print("\n🔐 String Session الخاص بك:")
        print("-" * 50)
        print(string_session)
        print("-" * 50)
        
        # حفظ في ملف
        await save_session_to_file(string_session, me)
        
        # تحديث ملف .env
        await update_env_file(api_id, api_hash, phone, string_session)
        
        print("\n📋 الخطوات التالية:")
        print("1. String Session تم حفظه في ملف .env تلقائياً")
        print("2. شغل البوت باستخدام: python run.py")
        print("3. أو شغل اختبار بسيط: python run.py --test")
        
        await client.disconnect()
        
        return string_session
        
    except Exception as e:
        print(f"\n❌ خطأ في إنشاء String Session: {e}")
        print("\n🔧 نصائح لحل المشكلة:")
        print("- تأكد من صحة API_ID و API_HASH")
        print("- تأكد من صحة رقم الهاتف")
        print("- تأكد من اتصالك بالإنترنت")
        print("- جرب مرة أخرى بعد بضع دقائق")
        return None

def get_api_credentials():
    """الحصول على بيانات API من المستخدم"""
    print("\n📋 للحصول على API_ID و API_HASH:")
    print("1. اذهب إلى: https://my.telegram.org/apps")
    print("2. سجل دخولك برقم هاتفك")
    print("3. أنشئ تطبيق جديد")
    print("4. انسخ API_ID و API_HASH")
    print()
    
    # محاولة قراءة من ملف .env إذا كان موجوداً
    env_file = Path('.env')
    if env_file.exists():
        print("🔍 تم العثور على ملف .env، جاري قراءة البيانات...")
        try:
            load_dotenv()
            
            api_id = os.getenv('API_ID')
            api_hash = os.getenv('API_HASH')
            
            if api_id and api_hash and api_id != 'your_api_id_here':
                print(f"✅ تم العثور على API_ID: {api_id}")
                print(f"✅ تم العثور على API_HASH: {api_hash[:8]}...")
                
                use_existing = input("\n🤔 هل تريد استخدام هذه البيانات؟ (y/n): ").lower()
                if use_existing in ['y', 'yes', 'نعم', '']:
                    return int(api_id), api_hash
        except Exception as e:
            print(f"⚠️ خطأ في قراءة ملف .env: {e}")
    
    # طلب البيانات يدوياً
    while True:
        try:
            api_id = input("📝 أدخل API_ID: ").strip()
            if not api_id:
                print("❌ API_ID مطلوب!")
                continue
            
            api_id = int(api_id)
            break
        except ValueError:
            print("❌ API_ID يجب أن يكون رقماً!")
    
    while True:
        api_hash = input("📝 أدخل API_HASH: ").strip()
        if not api_hash:
            print("❌ API_HASH مطلوب!")
            continue
        if len(api_hash) < 32:
            print("❌ API_HASH قصير جداً! يجب أن يكون 32 حرف على الأقل")
            continue
        break
    
    return api_id, api_hash

def get_phone_number():
    """الحصول على رقم الهاتف من المستخدم"""
    print("\n📱 إدخال رقم الهاتف:")
    print("💡 أدخل رقم الهاتف بالتنسيق الدولي (مثل: +1234567890)")
    
    while True:
        phone = input("📝 أدخل رقم الهاتف: ").strip()
        if not phone:
            print("❌ رقم الهاتف مطلوب!")
            continue
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # التحقق من صحة الرقم
        if len(phone) < 8 or not phone[1:].replace(' ', '').replace('-', '').isdigit():
            print("❌ رقم الهاتف غير صحيح!")
            continue
        
        print(f"📱 رقم الهاتف: {phone}")
        confirm = input("✅ هل الرقم صحيح؟ (y/n): ").lower()
        if confirm in ['y', 'yes', 'نعم', '']:
            return phone

async def save_session_to_file(string_session, user_info):
    """حفظ String Session في ملف"""
    try:
        session_file = Path('sessions') / 'string_session.txt'
        session_file.parent.mkdir(exist_ok=True)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(f"# String Session لبوت أرشفة تليغرام\n")
            f.write(f"# تم إنشاؤه في: {asyncio.get_event_loop().time()}\n")
            f.write(f"# الحساب: {user_info.first_name} (@{user_info.username or 'غير محدد'})\n")
            f.write(f"# ID: {user_info.id}\n\n")
            f.write(f"STRING_SESSION={string_session}\n")
        
        print(f"\n💾 تم حفظ String Session في: {session_file}")
        
    except Exception as e:
        print(f"⚠️ لم يتم حفظ الملف: {e}")

async def update_env_file(api_id, api_hash, phone, string_session):
    """تحديث ملف .env بالبيانات الجديدة"""
    try:
        env_file = Path('.env')
        
        # قراءة الملف الموجود أو إنشاء جديد
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""
        
        # تحديث أو إضافة المتغيرات
        lines = content.split('\n') if content else []
        updated_vars = {
            'API_ID': str(api_id),
            'API_HASH': api_hash,
            'PHONE_NUMBER': phone,
            'STRING_SESSION': string_session
        }
        
        # تحديث المتغيرات الموجودة أو إضافة جديدة
        for var, value in updated_vars.items():
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{var}="):
                    lines[i] = f"{var}={value}"
                    found = True
                    break
            
            if not found:
                lines.append(f"{var}={value}")
        
        # إضافة متغيرات أخرى إذا لم تكن موجودة
        default_vars = {
            'BOT_TOKEN': 'your_bot_token_here',
            'SOURCE_CHANNEL': '@your_channel_username',
            'ADMIN_IDS': '123456789,987654321',
            'DEBUG': 'false',
            'ENVIRONMENT': 'development'
        }
        
        for var, default_value in default_vars.items():
            found = any(line.startswith(f"{var}=") for line in lines)
            if not found:
                lines.append(f"{var}={default_value}")
        
        # حفظ الملف المحدث
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ تم تحديث ملف .env بنجاح")
        
    except Exception as e:
        print(f"⚠️ خطأ في تحديث ملف .env: {e}")

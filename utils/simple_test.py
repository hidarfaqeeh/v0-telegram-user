#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار بسيط لبوت تليغرام
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    from dotenv import load_dotenv
except ImportError:
    print("❌ المكتبات المطلوبة غير مثبتة")
    print("🔧 قم بتشغيل: python run.py --setup")
    sys.exit(1)

async def run_simple_test():
    """تشغيل اختبار بسيط للبوت"""
    print("🧪 اختبار بوت تليغرام البسيط")
    print("=" * 40)
    
    # تحميل متغيرات البيئة
    load_dotenv()
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip().isdigit()]
    
    if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
        print("❌ BOT_TOKEN غير محدد في ملف .env")
        return
    
    if not ADMIN_IDS:
        print("❌ ADMIN_IDS غير محدد في ملف .env")
        return
    
    print(f"🔑 رمز البوت: {BOT_TOKEN[:10]}...")
    print(f"👥 المدراء: {ADMIN_IDS}")
    
    def is_admin(user_id):
        """التحقق من صلاحيات المدير"""
        return user_id in ADMIN_IDS

    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ غير مصرح لك باستخدام هذا البوت")
            return
        
        welcome_text = f"""
🤖 **اختبار البوت - يعمل بنجاح!**

👋 مرحباً {update.effective_user.first_name}!

🆔 معرفك: `{user_id}`
⏰ الوقت: `{update.message.date}`

✅ البوت يستجيب بشكل طبيعي!

🔧 **أوامر الاختبار:**
• /ping - اختبار سرعة الاستجابة
• /info - معلومات البوت
• /test - اختبار شامل
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر اختبار سرعة الاستجابة"""
        if not is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("🏓 **Pong!** - البوت يعمل بسرعة!", parse_mode='Markdown')

    async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معلومات البوت"""
        if not is_admin(update.effective_user.id):
            return
        
        bot_info = await context.bot.get_me()
        
        info_text = f"""
ℹ️ **معلومات البوت:**

🤖 **الاسم:** {bot_info.first_name}
📧 **المعرف:** @{bot_info.username}
🆔 **ID:** `{bot_info.id}`
🔒 **يمكنه الانضمام للمجموعات:** {bot_info.can_join_groups}
📨 **يمكنه قراءة جميع الرسائل:** {bot_info.can_read_all_group_messages}

👥 **المدراء المصرح لهم:** {len(ADMIN_IDS)}
📁 **المجلد الحالي:** `{Path.cwd()}`
🐍 **إصدار Python:** `{sys.version.split()[0]}`
        """
        
        await update.message.reply_text(info_text, parse_mode='Markdown')

    async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختبار شامل"""
        if not is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("🔄 جاري تشغيل الاختبار الشامل...")
        
        # اختبار إرسال رسائل متعددة
        tests = [
            "✅ اختبار 1: إرسال رسالة نصية",
            "✅ اختبار 2: استخدام Markdown **بنجاح**",
            "✅ اختبار 3: الرموز التعبيرية 🎉",
            "✅ اختبار 4: الأرقام والتواريخ: 2025-05-29",
            "✅ اختبار 5: النص العربي يعمل بشكل طبيعي"
        ]
        
        for test in tests:
            await update.message.reply_text(test, parse_mode='Markdown')
            await asyncio.sleep(0.5)  # توقف قصير بين الرسائل
        
        await update.message.reply_text(
            "🎉 **انتهى الاختبار الشامل بنجاح!**\n\n"
            "✅ جميع الوظائف تعمل بشكل طبيعي\n"
            "🚀 يمكنك الآن تشغيل البوت الكامل: `python run.py`",
            parse_mode='Markdown'
        )

    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("test", test_command))
    
    print("✅ تم إعداد البوت بنجاح")
    print("🚀 البوت يعمل الآن... اضغط Ctrl+C للإيقاف")
    print("\n💡 جرب إرسال /start للبوت في تليغرام")
    print("⏹️ اضغط Ctrl+C لإيقاف الاختبار")
    
    # تشغيل البوت
    try:
        await app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف الاختبار")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل البوت: {e}")

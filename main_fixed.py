#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أرشفة تليغرام - نسخة مُصلحة لمشاكل asyncio
"""

import asyncio
import os
import sys
import signal
import logging
from pathlib import Path

# إصلاح مشاكل event loop
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("✅ تم تطبيق nest_asyncio")
except ImportError:
    print("⚠️ nest_asyncio غير مثبت - قد تحدث مشاكل في بعض البيئات")

# إضافة المجلد الحالي إلى مسار البحث
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد المكونات
from src.bot import TelegramArchiveBot
from utils.logger import setup_logging

def setup_signal_handlers():
    """إعداد معالجات الإشارات"""
    def signal_handler(signum, frame):
        print(f"\n⏹️ تم استلام إشارة {signum} - جاري الإيقاف...")
        # إيقاف جميع المهام
        for task in asyncio.all_tasks():
            task.cancel()
        sys.exit(0)
    
    # تسجيل معالجات الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def run_bot_safe():
    """تشغيل البوت بطريقة آمنة"""
    logger = setup_logging()
    
    try:
        # إنشاء البوت
        bot = TelegramArchiveBot()
        
        # تشغيل البوت
        logger.info("🚀 بدء تشغيل البوت...")
        success = await bot.run()
        
        if success:
            logger.info("✅ تم تشغيل البوت بنجاح")
        else:
            logger.error("❌ فشل في تشغيل البوت")
            return False
            
    except asyncio.CancelledError:
        logger.info("⏹️ تم إلغاء تشغيل البوت")
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """الدالة الرئيسية"""
    print("🤖 بوت أرشفة تليغرام - النسخة المُصلحة")
    print("=" * 50)
    
    # إعداد معالجات الإشارات
    setup_signal_handlers()
    
    # تشغيل البوت
    try:
        # التحقق من وجود event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # إنشاء loop جديد إذا كان مغلق
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # إنشاء loop جديد إذا لم يكن موجود
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # تشغيل البوت
        if loop.is_running():
            # إذا كان loop يعمل، استخدم create_task
            task = loop.create_task(run_bot_safe())
            loop.run_until_complete(task)
        else:
            # إذا لم يكن loop يعمل، استخدم run_until_complete
            loop.run_until_complete(run_bot_safe())
            
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت")
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # تنظيف
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                # إلغاء جميع المهام المعلقة
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # انتظار انتهاء المهام
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                loop.close()
        except Exception as e:
            print(f"⚠️ خطأ في التنظيف: {e}")

if __name__ == "__main__":
    main()

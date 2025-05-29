#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أرشفة تليغرام - نقطة البداية الرئيسية
يتحكم في تشغيل جميع مكونات البوت
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# إضافة المجلد الحالي إلى مسار البحث
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد المكونات
from src.bot import TelegramArchiveBot
from utils.setup import setup_environment, check_requirements
from utils.diagnostics import run_diagnostics
from utils.session_manager import create_string_session

def print_header():
    """طباعة رأس البرنامج"""
    print("\n" + "=" * 60)
    print("🤖 بوت أرشفة تليغرام - الإصدار 2.0")
    print("=" * 60)

def parse_arguments():
    """تحليل وسائط سطر الأوامر"""
    parser = argparse.ArgumentParser(description='بوت أرشفة تليغرام')
    
    parser.add_argument('--setup', action='store_true', help='إعداد البيئة والمتطلبات')
    parser.add_argument('--diagnostics', action='store_true', help='تشغيل أداة التشخيص')
    parser.add_argument('--session', action='store_true', help='إنشاء String Session')
    parser.add_argument('--test', action='store_true', help='تشغيل اختبار بسيط للبوت')
    parser.add_argument('--debug', action='store_true', help='تشغيل في وضع التصحيح')
    
    return parser.parse_args()

async def main():
    """الدالة الرئيسية"""
    print_header()
    
    # تحليل وسائط سطر الأوامر
    args = parse_arguments()
    
    # إعداد البيئة
    if args.setup:
        print("\n🔧 بدء إعداد البيئة...")
        setup_environment()
        sys.exit(0)
    
    # تشغيل أداة التشخيص
    if args.diagnostics:
        print("\n🔍 بدء تشخيص البوت...")
        await run_diagnostics()
        sys.exit(0)
    
    # إنشاء String Session
    if args.session:
        print("\n🔐 بدء إنشاء String Session...")
        await create_string_session()
        sys.exit(0)
    
    # تشغيل اختبار بسيط
    if args.test:
        print("\n🧪 بدء اختبار البوت البسيط...")
        from utils.simple_test import run_simple_test
        await run_simple_test()
        sys.exit(0)
    
    # التحقق من المتطلبات
    check_requirements()
    
    # إنشاء وتشغيل البوت
    print("\n🚀 بدء تشغيل بوت الأرشفة...")
    bot = TelegramArchiveBot(debug=args.debug)
    await bot.run()

if __name__ == "__main__":
    try:
        # تشغيل البوت
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()

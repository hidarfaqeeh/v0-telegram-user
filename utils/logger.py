#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام السجلات لبوت أرشفة تليغرام
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(debug=False):
    """إعداد نظام السجلات"""
    
    # إنشاء مجلد السجلات
    Path('logs').mkdir(exist_ok=True)
    
    # تحديد مستوى السجل
    log_level = logging.DEBUG if debug else logging.INFO
    
    # تنسيق السجل
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # إنشاء formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # إعداد السجل الرئيسي
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # إزالة المعالجات الموجودة
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # معالج الملف
    file_handler = logging.FileHandler(
        f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # معالج وحدة التحكم
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # تقليل مستوى سجلات المكتبات الخارجية
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger

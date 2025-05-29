#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير قاعدة البيانات مع دعم أنواع مختلفة
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير قاعدة البيانات الموحد"""
    
    def __init__(self, config):
        self.config = config
        self.db_type = config.database.db_type
        self.connection = None
        self.cursor = None
    
    async def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            if self.db_type == 'sqlite':
                await self._connect_sqlite()
            elif self.db_type == 'postgresql':
                await self._connect_postgresql()
            elif self.db_type == 'mysql':
                await self._connect_mysql()
            else:
                raise ValueError(f"نوع قاعدة البيانات غير مدعوم: {self.db_type}")
            
            # إنشاء الجداول
            await self._create_tables()
            
            logger.info(f"✅ تم الاتصال بقاعدة البيانات: {self.db_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
            return False
    
    async def _connect_sqlite(self):
        """الاتصال بـ SQLite"""
        import sqlite3
        
        db_file = self.config.database.connection_string
        
        # إنشاء مجلد قاعدة البيانات إذا لم يكن موجوداً
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
    
    async def _connect_postgresql(self):
        """الاتصال بـ PostgreSQL"""
        try:
            import asyncpg
        except ImportError:
            raise ImportError("يرجى تثبيت asyncpg: pip install asyncpg")
        
        conn_params = self.config.database.connection_string
        self.connection = await asyncpg.connect(**conn_params)
    
    async def _connect_mysql(self):
        """الاتصال بـ MySQL"""
        try:
            import aiomysql
        except ImportError:
            raise ImportError("يرجى تثبيت aiomysql: pip install aiomysql")
        
        conn_params = self.config.database.connection_string
        self.connection = await aiomysql.connect(**conn_params)
        self.cursor = await self.connection.cursor()
    
    async def _create_tables(self):
        """إنشاء الجداول المطلوبة"""
        if self.db_type == 'sqlite':
            await self._create_sqlite_tables()
        elif self.db_type == 'postgresql':
            await self._create_postgresql_tables()
        elif self.db_type == 'mysql':
            await self._create_mysql_tables()
    
    async def _create_sqlite_tables(self):
        """إنشاء جداول SQLite"""
        tables = [
            '''CREATE TABLE IF NOT EXISTS archived_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                channel_id INTEGER,
                date TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                content TEXT,
                media_type TEXT,
                file_id TEXT,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, channel_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_date ON archived_messages(date)',
            'CREATE INDEX IF NOT EXISTS idx_content ON archived_messages(content)',
            'CREATE INDEX IF NOT EXISTS idx_year_month_day ON archived_messages(year, month, day)'
        ]
        
        for table in tables:
            self.cursor.execute(table)
        
        for index in indexes:
            self.cursor.execute(index)
        
        self.connection.commit()
    
    async def _create_postgresql_tables(self):
        """إنشاء جداول PostgreSQL"""
        tables = [
            '''CREATE TABLE IF NOT EXISTS archived_messages (
                id SERIAL PRIMARY KEY,
                message_id BIGINT NOT NULL,
                channel_id BIGINT,
                date TIMESTAMP NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                content TEXT,
                media_type VARCHAR(50),
                file_id TEXT,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, channel_id)
            )''',
            
            '''CREATE TABLE IF NOT EXISTS settings (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_date ON archived_messages(date)',
            'CREATE INDEX IF NOT EXISTS idx_content ON archived_messages USING gin(to_tsvector(\'arabic\', content))',
            'CREATE INDEX IF NOT EXISTS idx_year_month_day ON archived_messages(year, month, day)'
        ]
        
        for table in tables:
            await self.connection.execute(table)
        
        for index in indexes:
            try:
                await self.connection.execute(index)
            except Exception as e:
                logger.warning(f"تحذير في إنشاء الفهرس: {e}")
    
    async def _create_mysql_tables(self):
        """إنشاء جداول MySQL"""
        tables = [
            '''CREATE TABLE IF NOT EXISTS archived_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message_id BIGINT NOT NULL,
                channel_id BIGINT,
                date DATETIME NOT NULL,
                year INT NOT NULL,
                month INT NOT NULL,
                day INT NOT NULL,
                content TEXT,
                media_type VARCHAR(50),
                file_id TEXT,
                file_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_message (message_id, channel_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
            
            '''CREATE TABLE IF NOT EXISTS settings (
                `key` VARCHAR(255) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''',
            
            '''CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'''
        ]
        
        indexes = [
            'CREATE INDEX idx_date ON archived_messages(date)',
            'CREATE FULLTEXT INDEX idx_content ON archived_messages(content)',
            'CREATE INDEX idx_year_month_day ON archived_messages(year, month, day)'
        ]
        
        for table in tables:
            await self.cursor.execute(table)
        
        for index in indexes:
            try:
                await self.cursor.execute(index)
            except Exception as e:
                logger.warning(f"تحذير في إنشاء الفهرس: {e}")
        
        await self.connection.commit()
    
    async def execute_query(self, query: str, params: tuple = None):
        """تنفيذ استعلام"""
        try:
            if self.db_type == 'sqlite':
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                self.connection.commit()
                return self.cursor.fetchall()
            
            elif self.db_type == 'postgresql':
                if params:
                    return await self.connection.fetch(query, *params)
                else:
                    return await self.connection.fetch(query)
            
            elif self.db_type == 'mysql':
                if params:
                    await self.cursor.execute(query, params)
                else:
                    await self.cursor.execute(query)
                await self.connection.commit()
                return await self.cursor.fetchall()
                
        except Exception as e:
            logger.error(f"❌ خطأ في تنفيذ الاستعلام: {e}")
            raise
    
    async def insert_message(self, message_data: Dict[str, Any]):
        """إدراج رسالة في قاعدة البيانات"""
        query = '''
            INSERT OR REPLACE INTO archived_messages 
            (message_id, channel_id, date, year, month, day, content, media_type, file_id, file_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''' if self.db_type == 'sqlite' else '''
            INSERT INTO archived_messages 
            (message_id, channel_id, date, year, month, day, content, media_type, file_id, file_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content = VALUES(content)
        ''' if self.db_type == 'mysql' else '''
            INSERT INTO archived_messages 
            (message_id, channel_id, date, year, month, day, content, media_type, file_id, file_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (message_id, channel_id) DO UPDATE SET content = EXCLUDED.content
        '''
        
        params = (
            message_data['message_id'],
            message_data['channel_id'],
            message_data['date'],
            message_data['year'],
            message_data['month'],
            message_data['day'],
            message_data['content'],
            message_data['media_type'],
            message_data['file_id'],
            message_data['file_name']
        )
        
        await self.execute_query(query, params)
    
    async def get_message_count(self):
        """الحصول على عدد الرسائل"""
        query = "SELECT COUNT(*) FROM archived_messages"
        result = await self.execute_query(query)
        
        if self.db_type == 'sqlite':
            return result[0][0]
        else:
            return result[0]['count'] if result else 0
    
    async def disconnect(self):
        """قطع الاتصال"""
        try:
            if self.connection:
                if self.db_type == 'sqlite':
                    self.connection.close()
                else:
                    await self.connection.close()
            logger.info("✅ تم قطع الاتصال بقاعدة البيانات")
        except Exception as e:
            logger.error(f"❌ خطأ في قطع الاتصال: {e}")

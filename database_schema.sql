-- جدول الرسائل المؤرشفة
CREATE TABLE archived_messages (
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
);

-- جدول الإعدادات
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول المدراء
CREATE TABLE admins (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- فهارس للبحث السريع
CREATE INDEX idx_date ON archived_messages(date);
CREATE INDEX idx_content ON archived_messages(content);
CREATE INDEX idx_year_month_day ON archived_messages(year, month, day);

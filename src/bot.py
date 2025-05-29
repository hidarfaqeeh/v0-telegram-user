#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت أرشفة تليغرام - الفئة الرئيسية
"""
import asyncio
import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# إعداد تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.bot_app = ApplicationBuilder().token(self.token).build()

    def add_handler(self, handler):
        self.bot_app.add_handler(handler)

    async def start(self):
        await self.bot_app.initialize()

    async def run(self):
        # تشغيل Bot
        async with self.bot_app:
            await self.bot_app.start()
            await self.bot_app.updater.start_polling(drop_pending_updates=True)
            
            # انتظار إيقاف البوت
            try:
                # إبقاء البوت يعمل
                await asyncio.Event().wait()
            except (KeyboardInterrupt, asyncio.CancelledError):
                logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
            finally:
                await self.bot_app.updater.stop()
                await self.bot_app.stop()
        
        # تحميل الإعدادات
        self.config = Config()
        
        # إنشاء المجلدات المطلوبة
        self.create_directories()
        
        # إعداد قاعدة البيانات
        self.init_database()
        
        # متغيرات العملاء
        self.userbot = None
        self.bot_app = None
        self.is_running = False
        
        logger.info("✅ تم تهيئة البوت بنجاح")

    def create_directories(self):
        """إنشاء المجلدات المطلوبة"""
        directories = ['archive', 'exports', 'backups', 'logs', 'config', 'sessions']
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        logger.info("📁 تم إنشاء المجلدات المطلوبة")

    def init_database(self):
        """إنشاء قاعدة البيانات وجداولها"""
        try:
            self.conn = sqlite3.connect('archive.db', check_same_thread=False)
            cursor = self.conn.cursor()
            
            # جدول الرسائل المؤرشفة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archived_messages (
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
                )
            ''')
            
            # جدول الإعدادات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول المدراء
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء فهارس للبحث السريع
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON archived_messages(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_content ON archived_messages(content)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_year_month_day ON archived_messages(year, month, day)')
            
            self.conn.commit()
            logger.info("✅ تم إعداد قاعدة البيانات بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
            raise

    async def start_userbot(self):
        """بدء تشغيل Userbot مع دعم String Session"""
        if not all([self.config.API_ID, self.config.API_HASH]):
            logger.error("❌ API_ID و API_HASH مطلوبان لتشغيل Userbot")
            return False
        
        try:
            # استخدام String Session إذا كان متوفراً
            if self.config.STRING_SESSION:
                logger.info("🔐 استخدام String Session للاتصال...")
                session = StringSession(self.config.STRING_SESSION)
            else:
                logger.info("📱 استخدام رقم الهاتف للاتصال...")
                session = 'sessions/userbot'
            
            self.userbot = TelegramClient(session, self.config.API_ID, self.config.API_HASH)
            
            # بدء الاتصال
            if self.config.STRING_SESSION:
                await self.userbot.start()
            else:
                await self.userbot.start(phone=self.config.PHONE_NUMBER)
            
            # التحقق من الاتصال
            me = await self.userbot.get_me()
            logger.info(f"✅ تم تشغيل Userbot بنجاح - {me.first_name}")
            
            # إعداد مراقب الرسائل الجديدة
            if self.config.SOURCE_CHANNEL:
                @self.userbot.on(events.NewMessage(chats=self.config.SOURCE_CHANNEL))
                async def handle_new_message(event):
                    await self.archive_message(event.message)
                    logger.info(f"📥 تم أرشفة رسالة جديدة: {event.message.id}")
                
                logger.info(f"👀 بدء مراقبة القناة: {self.config.SOURCE_CHANNEL}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل Userbot: {e}")
            if "STRING_SESSION" in str(e) or "session" in str(e).lower():
                logger.error("💡 نصيحة: تشغيل python run.py --session لإنشاء String Session جديد")
            return False

    async def start_bot(self):
        """بدء تشغيل Bot"""
        if not self.config.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN مطلوب لتشغيل Bot")
            return False
        
        try:
            self.bot_app = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # إضافة معالجات الأوامر
            handlers = [
                CommandHandler("start", self.cmd_start),
                CommandHandler("help", self.cmd_help),
                CommandHandler("status", self.cmd_status),
                CommandHandler("archive_today", self.cmd_archive_today),
                CommandHandler("archive_day", self.cmd_archive_day),
                CommandHandler("browse", self.cmd_browse),
                CommandHandler("search", self.cmd_search),
                CommandHandler("export", self.cmd_export),
                CommandHandler("set_channel", self.cmd_set_channel),
                CommandHandler("diagnostics", self.cmd_diagnostics),
                CallbackQueryHandler(self.handle_callback),
            ]
            
            for handler in handlers:
                self.bot_app.add_handler(handler)
            
            logger.info("✅ تم إعداد Bot بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد Bot: {e}")
            return False

    async def archive_message(self, message):
        """أرشفة رسالة واحدة"""
        try:
            msg_date = message.date
            year = msg_date.year
            month = msg_date.month
            day = msg_date.day
            
            # تحضير بيانات الرسالة
            content = message.text or message.caption or ""
            media_type = None
            file_id = None
            file_name = None
            
            # معالجة الوسائط
            if message.media:
                if message.photo:
                    media_type = "photo"
                    file_id = str(message.photo.id)
                elif message.video:
                    media_type = "video"
                    file_id = str(message.video.id)
                    file_name = getattr(message.video, 'file_name', None)
                elif message.document:
                    media_type = "document"
                    file_id = str(message.document.id)
                    file_name = getattr(message.document, 'file_name', None)
                elif message.audio:
                    media_type = "audio"
                    file_id = str(message.audio.id)
                    file_name = getattr(message.audio, 'file_name', None)
            
            # حفظ في قاعدة البيانات
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO archived_messages 
                (message_id, channel_id, date, year, month, day, content, media_type, file_id, file_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.id,
                message.chat_id,
                msg_date.isoformat(),
                year, month, day,
                content,
                media_type,
                file_id,
                file_name
            ))
            self.conn.commit()
            
            # حفظ في ملف JSON
            await self.save_to_json_file(year, month, day, {
                'message_id': message.id,
                'date': msg_date.isoformat(),
                'content': content,
                'media_type': media_type,
                'file_id': file_id,
                'file_name': file_name
            })
            
        except Exception as e:
            logger.error(f"❌ خطأ في أرشفة الرسالة {message.id}: {e}")

    async def save_to_json_file(self, year: int, month: int, day: int, message_data: dict):
        """حفظ الرسالة في ملف JSON"""
        try:
            # إنشاء مسار الملف
            year_dir = Path('archive') / str(year)
            month_dir = year_dir / f"{month:02d}"
            month_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = month_dir / f"{day:02d}.json"
            
            # قراءة البيانات الموجودة
            messages = []
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            messages = json.loads(content)
                except (json.JSONDecodeError, FileNotFoundError):
                    messages = []
            
            # إضافة الرسالة الجديدة
            messages.append(message_data)
            
            # حفظ الملف
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ ملف JSON: {e}")

    def is_admin(self, user_id: int) -> bool:
        """التحقق من صلاحيات المدير"""
        return user_id in self.config.ADMIN_IDS

    # معالجات الأوامر
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ غير مصرح لك باستخدام هذا البوت")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="status")],
            [InlineKeyboardButton("📅 تصفح الأرشيف", callback_data="browse")],
            [InlineKeyboardButton("🔍 البحث", callback_data="search_menu")],
            [InlineKeyboardButton("⚙️ المساعدة", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 **مرحباً بك في بوت أرشفة تليغرام**

👋 أهلاً {update.effective_user.first_name}!

📋 **الوظائف المتاحة:**
• 🔄 أرشفة تلقائية للقناة المحددة
• 📅 أرشفة يدوية بتواريخ مخصصة  
• 🗂️ تصفح الأرشيف بطريقة تفاعلية
• 🔍 البحث في المحتوى المؤرشف
• 📤 تصدير واستيراد البيانات

📊 **الحالة الحالية:**
• القناة المصدر: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}

اختر من القائمة أدناه للبدء:
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        help_text = """
🆘 **دليل استخدام البوت:**

**📁 أوامر الأرشفة:**
• `/archive_today` - أرشفة منشورات اليوم
• `/archive_day YYYY-MM-DD` - أرشفة يوم محدد

**📊 أوامر المعلومات:**
• `/status` - عرض إحصائيات الأرشيف
• `/browse` - تصفح الأرشيف تفاعلياً

**🔍 البحث:**
• `/search كلمة البحث` - البحث في المحتوى

**⚙️ الإدارة:**
• `/set_channel @channel` - تحديد القناة المصدر
• `/export YYYY-MM-DD` - تصدير أرشيف يوم
• `/diagnostics` - تشخيص مشاكل البوت

**💡 نصائح:**
- استخدم الأزرار التفاعلية للتنقل السهل
- يمكن البحث في النصوص والتسميات التوضيحية
- الأرشفة التلقائية تعمل في الخلفية

**🔗 روابط مفيدة:**
- احصل على API من: https://my.telegram.org/apps
- أنشئ بوت جديد: @BotFather
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض إحصائيات الأرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        try:
            cursor = self.conn.cursor()
            
            # إجمالي الرسائل
            cursor.execute("SELECT COUNT(*) FROM archived_messages")
            total_messages = cursor.fetchone()[0]
            
            # رسائل اليوم
            today = datetime.now().date()
            cursor.execute(
                "SELECT COUNT(*) FROM archived_messages WHERE date LIKE ?",
                (f"{today}%",)
            )
            today_messages = cursor.fetchone()[0]
            
            # رسائل هذا الشهر
            this_month = today.strftime("%Y-%m")
            cursor.execute(
                "SELECT COUNT(*) FROM archived_messages WHERE date LIKE ?",
                (f"{this_month}%",)
            )
            month_messages = cursor.fetchone()[0]
            
            # أحدث رسالة
            cursor.execute(
                "SELECT date FROM archived_messages ORDER BY date DESC LIMIT 1"
            )
            latest = cursor.fetchone()
            latest_date = latest[0] if latest else "لا توجد رسائل"
            
            # حجم قاعدة البيانات
            db_size = Path('archive.db').stat().st_size / (1024 * 1024)  # MB
            
            status_text = f"""
📊 **إحصائيات الأرشيف:**

📈 **الرسائل:**
• إجمالي الرسائل: `{total_messages:,}`
• رسائل اليوم: `{today_messages:,}`
• رسائل هذا الشهر: `{month_messages:,}`

🕐 **التوقيت:**
• آخر رسالة مؤرشفة: `{latest_date}`
• وقت التحديث: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

⚙️ **النظام:**
• القناة المصدر: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
• حجم قاعدة البيانات: `{db_size:.2f} MB`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}
• Bot: {'🟢 يعمل' if self.is_running else '🔴 متوقف'}
            """
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في جلب الإحصائيات: {e}")

    async def cmd_browse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصفح الأرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT year FROM archived_messages ORDER BY year DESC")
            years = [row[0] for row in cursor.fetchall()]
            
            if not years:
                await update.message.reply_text("📭 لا توجد رسائل مؤرشفة بعد")
                return
            
            keyboard = []
            for year in years:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ?", (year,)
                )
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 {year} ({count:,} رسالة)",
                        callback_data=f"browse_year_{year}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📂 اختر السنة للتصفح:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في تصفح الأرشيف: {e}")

    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """البحث في الأرشيف"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔍 **استخدم:** `/search كلمة البحث`\n"
                "**مثال:** `/search مرحبا`",
                parse_mode='Markdown'
            )
            return
        
        search_term = " ".join(context.args)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT message_id, date, content, media_type 
                   FROM archived_messages 
                   WHERE content LIKE ? 
                   ORDER BY date DESC LIMIT 20""",
                (f"%{search_term}%",)
            )
            results = cursor.fetchall()
            
            if not results:
                await update.message.reply_text(f"❌ لم يتم العثور على نتائج لـ: **{search_term}**", parse_mode='Markdown')
                return
            
            response = f"🔍 **نتائج البحث عن:** `{search_term}`\n\n"
            
            for i, (msg_id, date, content, media_type) in enumerate(results[:10], 1):
                preview = content[:100] + "..." if len(content) > 100 else content
                media_icon = {"photo": "🖼️", "video": "🎥", "document": "📄", "audio": "🎵"}.get(media_type, "💬")
                
                response += f"{i}. {media_icon} **{date[:10]}**\n"
                response += f"   `{preview}`\n\n"
            
            if len(results) > 10:
                response += f"... و {len(results) - 10} نتيجة أخرى"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في البحث: {e}")

    async def cmd_archive_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة منشورات اليوم"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        await update.message.reply_text("🔄 جاري أرشفة منشورات اليوم...")
        
        try:
            today = datetime.now().date()
            count = await self.archive_date_range(today, today)
            await update.message.reply_text(f"✅ تم أرشفة **{count}** رسالة من اليوم", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def cmd_archive_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أرشفة يوم محدد"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📅 **استخدم:** `/archive_day YYYY-MM-DD`\n"
                "**مثال:** `/archive_day 2025-05-29`",
                parse_mode='Markdown'
            )
            return
        
        try:
            date_str = context.args[0]
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            await update.message.reply_text(f"🔄 جاري أرشفة **{date_str}**...", parse_mode='Markdown')
            count = await self.archive_date_range(target_date, target_date)
            await update.message.reply_text(f"✅ تم أرشفة **{count}** رسالة من **{date_str}**", parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق التاريخ غير صحيح. استخدم: **YYYY-MM-DD**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في الأرشفة: {e}")

    async def archive_date_range(self, start_date, end_date) -> int:
        """أرشفة نطاق من التواريخ"""
        if not self.userbot or not self.config.SOURCE_CHANNEL:
            return 0
        
        count = 0
        try:
            async for message in self.userbot.iter_messages(
                self.config.SOURCE_CHANNEL,
                offset_date=end_date + timedelta(days=1),
                reverse=True
            ):
                if message.date.date() < start_date:
                    break
                if message.date.date() <= end_date:
                    await self.archive_message(message)
                    count += 1
                    
                    # تحديث كل 100 رسالة
                    if count % 100 == 0:
                        logger.info(f"📊 تم أرشفة {count} رسالة...")
                        
        except Exception as e:
            logger.error(f"❌ خطأ في أرشفة النطاق: {e}")
        
        return count

    async def cmd_set_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحديد القناة المصدر"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **استخدم:** `/set_channel @channel_username`\n"
                "**أو:** `/set_channel channel_id`\n"
                "**مثال:** `/set_channel @my_channel`",
                parse_mode='Markdown'
            )
            return
        
        channel = context.args[0]
        self.config.SOURCE_CHANNEL = channel
        
        # حفظ في قاعدة البيانات
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("source_channel", channel)
            )
            self.conn.commit()
            
            await update.message.reply_text(f"✅ تم تحديد القناة المصدر: **{channel}**", parse_mode='Markdown')
            
            # إعادة تشغيل مراقب الرسائل
            if self.userbot and self.userbot.is_connected():
                await update.message.reply_text("🔄 جاري إعادة تشغيل مراقب الرسائل...")
                
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في حفظ الإعدادات: {e}")

    async def cmd_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تصدير أرشيف يوم كملف JSON"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📤 **استخدم:** `/export YYYY-MM-DD`\n"
                "**مثال:** `/export 2025-05-29`",
                parse_mode='Markdown'
            )
            return
        
        try:
            date_str = context.args[0]
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # جلب رسائل اليوم
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT * FROM archived_messages 
                   WHERE date LIKE ? 
                   ORDER BY date""",
                (f"{date_str}%",)
            )
            
            rows = cursor.fetchall()
            
            if not rows:
                await update.message.reply_text(f"❌ لا توجد رسائل في **{date_str}**", parse_mode='Markdown')
                return
            
            # تحضير البيانات
            messages = []
            for row in rows:
                messages.append({
                    'message_id': row[1],
                    'channel_id': row[2],
                    'date': row[3],
                    'content': row[6],
                    'media_type': row[7],
                    'file_id': row[8],
                    'file_name': row[9]
                })
            
            # إنشاء ملف JSON
            export_data = {
                'date': date_str,
                'total_messages': len(messages),
                'exported_at': datetime.now().isoformat(),
                'source_channel': self.config.SOURCE_CHANNEL,
                'messages': messages
            }
            
            # حفظ في مجلد التصدير
            exports_dir = Path('exports')
            exports_dir.mkdir(exist_ok=True)
            
            filename = exports_dir / f"archive_{date_str}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # إرسال الملف
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"archive_{date_str}.json",
                    caption=f"📤 **أرشيف {date_str}**\n📊 **{len(messages)}** رسالة",
                    parse_mode='Markdown'
                )
            
            logger.info(f"📤 تم تصدير أرشيف {date_str} - {len(messages)} رسالة")
            
        except ValueError:
            await update.message.reply_text("❌ تنسيق التاريخ غير صحيح. استخدم: **YYYY-MM-DD**", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في التصدير: {e}")

    async def cmd_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تشغيل تشخيص البوت"""
        if not self.is_admin(update.effective_user.id):
            return
        
        await update.message.reply_text("🔍 جاري تشغيل التشخيص... قد يستغرق هذا بضع ثوان.")
        
        try:
            from utils.diagnostics import run_quick_diagnostics
            
            # تشغيل التشخيص السريع
            results = await run_quick_diagnostics(self.config)
            
            # إنشاء تقرير
            report = "📊 **نتائج التشخيص:**\n\n"
            
            # إضافة نتائج الفحوصات
            for check, status in results['checks'].items():
                icon = "✅" if status['success'] else "❌"
                report += f"{icon} **{check}**: {status['message']}\n"
            
            # إضافة الأخطاء
            if results['errors']:
                report += "\n❌ **الأخطاء:**\n"
                for error in results['errors']:
                    report += f"- {error}\n"
            
            # إضافة التحذيرات
            if results['warnings']:
                report += "\n⚠️ **التحذيرات:**\n"
                for warning in results['warnings']:
                    report += f"- {warning}\n"
            
            # إضافة الاقتراحات
            if results['suggestions']:
                report += "\n💡 **الاقتراحات:**\n"
                for suggestion in results['suggestions']:
                    report += f"- {suggestion}\n"
            
            # إرسال التقرير
            await update.message.reply_text(report, parse_mode='Markdown')
            
            # إرسال تقرير مفصل إذا كان هناك أخطاء
            if results['errors']:
                await update.message.reply_text(
                    "🔧 **لتشخيص أكثر تفصيلاً:**\n"
                    "شغل `python run.py --diagnostics` في الطرفية",
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في تشغيل التشخيص: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            return
        
        data = query.data
        
        try:
            if data == "status":
                await self.show_status_callback(query)
            elif data == "browse":
                await self.show_browse_callback(query)
            elif data == "help":
                await self.show_help_callback(query)
            elif data.startswith("browse_year_"):
                year = int(data.split("_")[-1])
                await self.show_months_callback(query, year)
            elif data.startswith("browse_month_"):
                parts = data.split("_")
                year, month = int(parts[2]), int(parts[3])
                await self.show_days_callback(query, year, month)
            elif data.startswith("browse_day_"):
                parts = data.split("_")
                year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
                await self.show_day_messages(query, year, month, day)
            elif data == "main_menu":
                await self.show_main_menu(query)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الزر: {e}")
            await query.edit_message_text(f"❌ حدث خطأ: {e}")

    async def show_main_menu(self, query):
        """عرض القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="status")],
            [InlineKeyboardButton("📅 تصفح الأرشيف", callback_data="browse")],
            [InlineKeyboardButton("🔍 البحث", callback_data="search_menu")],
            [InlineKeyboardButton("⚙️ المساعدة", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🤖 **مرحباً بك في بوت أرشفة تليغرام**

📋 **الوظائف المتاحة:**
• 🔄 أرشفة تلقائية للقناة المحددة
• 📅 أرشفة يدوية بتواريخ مخصصة  
• 🗂️ تصفح الأرشيف بطريقة تفاعلية
• 🔍 البحث في المحتوى المؤرشف
• 📤 تصدير واستيراد البيانات

📊 **الحالة الحالية:**
• القناة المصدر: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
• Userbot: {'🟢 متصل' if self.userbot and self.userbot.is_connected() else '🔴 غير متصل'}

اختر من القائمة أدناه للبدء:
        """
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_status_callback(self, query):
        """عرض الإحصائيات عبر الزر"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM archived_messages")
            total = cursor.fetchone()[0]
            
            today = datetime.now().date()
            cursor.execute("SELECT COUNT(*) FROM archived_messages WHERE date LIKE ?", (f"{today}%",))
            today_count = cursor.fetchone()[0]
            
            status_text = f"""
📊 **إحصائيات سريعة:**

📈 إجمالي الرسائل: `{total:,}`
📅 رسائل اليوم: `{today_count:,}`
📂 القناة: `{self.config.SOURCE_CHANNEL or 'غير محددة'}`
🤖 الحالة: {'🟢 يعمل' if self.is_running else '🔴 متوقف'}

🕐 آخر تحديث: `{datetime.now().strftime('%H:%M:%S')}`
            """
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في جلب الإحصائيات: {e}")

    async def show_browse_callback(self, query):
        """عرض قائمة السنوات"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT year FROM archived_messages ORDER BY year DESC")
            years = [row[0] for row in cursor.fetchall()]
            
            if not years:
                await query.edit_message_text("📭 لا توجد رسائل مؤرشفة")
                return
            
            keyboard = []
            for year in years:
                cursor.execute("SELECT COUNT(*) FROM archived_messages WHERE year = ?", (year,))
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"📅 {year} ({count:,} رسالة)",
                        callback_data=f"browse_year_{year}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text("📂 اختر السنة:", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في التصفح: {e}")

    async def show_help_callback(self, query):
        """عرض المساعدة عبر الزر"""
        help_text = """
🆘 **مساعدة سريعة:**

**📁 الأرشفة:**
• `/archive_today` - أرشفة اليوم
• `/archive_day YYYY-MM-DD` - أرشفة يوم محدد

**🔍 البحث:**
• `/search كلمة` - البحث في المحتوى

**⚙️ الإدارة:**
• `/status` - الإحصائيات
• `/set_channel @channel` - تحديد القناة
• `/export YYYY-MM-DD` - تصدير أرشيف
• `/diagnostics` - تشخيص المشاكل

💡 **نصيحة:** استخدم الأزرار للتنقل السهل!
        """
        
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_months_callback(self, query, year: int):
        """عرض شهور السنة"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT month FROM archived_messages WHERE year = ? ORDER BY month",
                (year,)
            )
            months = [row[0] for row in cursor.fetchall()]
            
            keyboard = []
            month_names = [
                "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
            ]
            
            for month in months:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ? AND month = ?",
                    (year, month)
                )
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗓️ {month_names[month-1]} ({count:,})",
                        callback_data=f"browse_month_{year}_{month}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="browse")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(f"📅 شهور عام {year}:", reply_markup=reply_markup)
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في عرض الشهور: {e}")

    async def show_days_callback(self, query, year: int, month: int):
        """عرض أيام الشهر"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT day FROM archived_messages WHERE year = ? AND month = ? ORDER BY day",
                (year, month)
            )
            days = [row[0] for row in cursor.fetchall()]
            
            keyboard = []
            for day in days:
                cursor.execute(
                    "SELECT COUNT(*) FROM archived_messages WHERE year = ? AND month = ? AND day = ?",
                    (year, month, day)
                )
                count = cursor.fetchone()[0]
                keyboard.append([
                    InlineKeyboardButton(
                        f"📆 {day:02d} ({count:,})",
                        callback_data=f"browse_day_{year}_{month}_{day}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data=f"browse_year_{year}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            month_names = [
                "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
            ]
            
            await query.edit_message_text(
                f"🗓️ أيام {month_names[month-1]} {year}:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في عرض الأيام: {e}")

    async def show_day_messages(self, query, year: int, month: int, day: int):
        """عرض رسائل اليوم"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT content, media_type, file_name FROM archived_messages 
                   WHERE year = ? AND month = ? AND day = ? 
                   ORDER BY date LIMIT 10""",
                (year, month, day)
            )
            messages = cursor.fetchall()
            
            if not messages:
                await query.edit_message_text("❌ لا توجد رسائل في هذا اليوم")
                return
            
            response = f"📅 **رسائل {day:02d}/{month:02d}/{year}**\n\n"
            
            for i, (content, media_type, file_name) in enumerate(messages, 1):
                media_icon = {
                    "photo": "🖼️", "video": "🎥", 
                    "document": "📄", "audio": "🎵"
                }.get(media_type, "💬")
                
                preview = content[:50] + "..." if len(content) > 50 else content
                response += f"{i}. {media_icon} `{preview}`\n"
            
            if len(messages) == 10:
                response += "\n... (عرض أول 10 رسائل)"
            
            keyboard = [[
                InlineKeyboardButton("🔙 العودة", callback_data=f"browse_month_{year}_{month}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطأ في عرض الرسائل: {e}")

    async def run(self):
        """تشغيل البوت الرئيسي"""
        logger.info("🚀 بدء تشغيل بوت الأرشفة...")
        
        # التحقق من الإعدادات
        if not self.config.validate():
            logger.error("❌ يرجى تعديل ملف .env وإضافة القيم الصحيحة")
            logger.error("💡 أو تشغيل: python run.py --setup")
            return False
        
        self.is_running = True
        
        try:
            # بدء Userbot
            logger.info("🔄 بدء تشغيل Userbot...")
            userbot_success = await self.start_userbot()
            
            if not userbot_success:
                logger.warning("⚠️ فشل في تشغيل Userbot - ستعمل الأوامر اليدوية فقط")
                logger.warning("💡 تشغيل: python run.py --session لإنشاء String Session")
            
            # بدء Bot
            logger.info("🔄 بدء تشغيل Bot...")
            bot_success = await self.start_bot()
            
            if not bot_success:
                logger.error("❌ فشل في تشغيل Bot")
                return False
            
            logger.info("✅ تم تشغيل البوت بنجاح!")
            logger.info("📱 Userbot: " + ("متصل ويراقب الرسائل الجديدة" if userbot_success else "غير متصل"))
            logger.info("🤖 Bot: جاهز لاستقبال الأوامر")
            
            # تشغيل Bot
            await self.bot_app.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
            
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
            if self.debug:
                import traceback
                logger.error(traceback.format_exc())
        finally:
            self.is_running = False
            if self.userbot:
                await self.userbot.disconnect()
            if self.conn:
                self.conn.close()
            logger.info("🔚 تم إغلاق البوت")

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.constants import ParseMode
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramArchiveBot:
    def __init__(self, config, db, userbot,debug=False):
        self.config = config
        self.db = db
        self.userbot = userbot
        self.application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
        self.job_queue = self.application.job_queue
        self.register_handlers()

    def register_handlers(self):
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("set_channel", self.cmd_set_channel))
        self.application.add_handler(CommandHandler("set_keyword", self.cmd_set_keyword))
        self.application.add_handler(CommandHandler("set_archive_chat", self.cmd_set_archive_chat))
        self.application.add_handler(CommandHandler("diagnostics", self.cmd_diagnostics))
        self.application.add_handler(CommandHandler("test_channel", self.cmd_test_channel))
        self.application.add_handler(CommandHandler("channel_info", self.cmd_channel_info))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sends a welcome message and instructions."""
        await update.message.reply_text(
            "مرحباً! أنا هنا لمساعدتك في أرشفة رسائل قناتك تلقائيًا.\n\n"
            "استخدم الأوامر التالية:\n"
            "/help - لعرض قائمة الأوامر المتاحة.\n"
            "/set_channel @اسم_القناة - لتعيين القناة التي سيتم أرشفة رسائلها.\n"
            "/set_keyword الكلمة_المفتاحية - لتعيين الكلمة المفتاحية لتفعيل الأرشفة.\n"
            "/set_archive_chat @اسم_المجموعة - لتعيين المجموعة التي سيتم إرسال الرسائل المؤرشفة إليها.\n"
            "/diagnostics - للتحقق من الإعدادات الحالية."
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sends a list of available commands."""
        await update.message.reply_text(
            "قائمة الأوامر المتاحة:\n"
            "/start - عرض رسالة الترحيب والتعليمات.\n"
            "/help - عرض هذه القائمة من الأوامر.\n"
            "/set_channel @اسم_القناة - تعيين القناة التي سيتم أرشفة رسائلها.\n"
            "/set_keyword الكلمة_المفتاحية - تعيين الكلمة المفتاحية لتفعيل الأرشفة.\n"
            "/set_archive_chat @اسم_المجموعة - تعيين المجموعة التي سيتم إرسال الرسائل المؤرشفة إليها.\n"
            "/diagnostics - التحقق من الإعدادات الحالية.\n"
            "/test_channel - اختبار الاتصال بالقناة وعرض معلومات مفصلة.\n"
            "/channel_info - عرض معلومات مفصلة عن القناة."
        )

    async def cmd_set_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sets the source channel to archive messages from."""
        if not self.is_admin(update.effective_user.id):
            return

        try:
            channel_username = context.args[0]
            self.config.SOURCE_CHANNEL = channel_username
            self.db.update_config("SOURCE_CHANNEL", channel_username)
            await update.message.reply_text(f"تم تعيين القناة المصدر إلى: {channel_username}")
        except (IndexError, ValueError):
            await update.message.reply_text("الرجاء تحديد اسم القناة. مثال: /set_channel @اسم_القناة")

    async def cmd_set_keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sets the keyword that triggers archiving."""
        if not self.is_admin(update.effective_user.id):
            return

        try:
            keyword = context.args[0]
            self.config.KEYWORD = keyword
            self.db.update_config("KEYWORD", keyword)
            await update.message.reply_text(f"تم تعيين الكلمة المفتاحية إلى: {keyword}")
        except (IndexError, ValueError):
            await update.message.reply_text("الرجاء تحديد الكلمة المفتاحية. مثال: /set_keyword الكلمة_المفتاحية")

    async def cmd_set_archive_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sets the chat to send archived messages to."""
        if not self.is_admin(update.effective_user.id):
            return

        try:
            chat_username = context.args[0]
            self.config.ARCHIVE_CHAT = chat_username
            self.db.update_config("ARCHIVE_CHAT", chat_username)
            await update.message.reply_text(f"تم تعيين دردشة الأرشيف إلى: {chat_username}")
        except (IndexError, ValueError):
            await update.message.reply_text("الرجاء تحديد اسم دردشة الأرشيف. مثال: /set_archive_chat @اسم_المجموعة")

    async def cmd_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays the current configuration settings."""
        if not self.is_admin(update.effective_user.id):
            return

        await update.message.reply_text(
            "الإعدادات الحالية:\n"
            f"القناة المصدر: {self.config.SOURCE_CHANNEL}\n"
            f"الكلمة المفتاحية: {self.config.KEYWORD}\n"
            f"دردشة الأرشيف: {self.config.ARCHIVE_CHAT}"
        )

    async def cmd_test_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اختبار الاتصال بالقناة وعرض معلومات مفصلة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر. استخدم `/set_channel @channel`")
            return
        
        await update.message.reply_text("🔍 جاري اختبار الاتصال بالقناة...")
        
        try:
            # اختبار الوصول للقناة
            entity = await self.userbot.get_entity(self.config.SOURCE_CHANNEL)
            
            # جلب معلومات العضوية
            try:
                participant = await self.userbot.get_permissions(entity)
                permissions_info = f"""
📋 **صلاحيات العضوية:**
• قراءة الرسائل: {'✅' if participant.view_messages else '❌'}
• إرسال الرسائل: {'✅' if participant.send_messages else '❌'}
• قراءة التاريخ: {'✅' if participant.view_messages else '❌'}
• نوع العضوية: `{type(participant).__name__}`
            """
            except Exception as e:
                permissions_info = f"⚠️ لا يمكن جلب معلومات الصلاحيات: {e}"
            
            # جلب آخر 5 رسائل للاختبار
            messages = []
            message_count = 0
            try:
                async for message in self.userbot.iter_messages(self.config.SOURCE_CHANNEL, limit=5):
                    message_count += 1
                    messages.append({
                        'id': message.id,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'content': (message.text or message.caption or '[وسائط]')[:50] + '...' if (message.text or message.caption) else '[وسائط بدون نص]',
                        'media': 'نعم' if message.media else 'لا'
                    })
            except Exception as e:
                messages_error = f"❌ خطأ في جلب الرسائل: {e}"
            
            # تحضير التقرير
            report = f"""
🔍 **تقرير اختبار القناة:**

✅ **معلومات القناة:**
• الاسم: `{entity.title}`
• المعرف: `{entity.id}`
• النوع: `{type(entity).__name__}`
• المعرف المدخل: `{self.config.SOURCE_CHANNEL}`
• عدد الأعضاء: `{getattr(entity, 'participants_count', 'غير متوفر')}`

{permissions_info}

📊 **اختبار جلب الرسائل:**
• تم جلب: `{len(messages)}` رسالة من آخر 5 رسائل
• حالة الاتصال: ✅ متصل

📝 **آخر الرسائل:**
        """
            
            if messages:
                for i, msg in enumerate(messages, 1):
                    report += f"\n{i}. `{msg['date']}` - ID: `{msg['id']}`"
                    report += f"\n   📄 المحتوى: {msg['content']}"
                    report += f"\n   📎 وسائط: {msg['media']}"
            else:
                report += "\n❌ لا توجد رسائل أو لا يمكن الوصول إليها"
            
            # اختبار أرشفة رسالة واحدة
            if messages:
                test_msg = messages[0]
                report += f"\n\n🧪 **اختبار الأرشفة:**\n"
                report += f"• جاري اختبار أرشفة الرسالة `{test_msg['id']}`..."
            
                await update.message.reply_text(report, parse_mode='Markdown')
            
                # محاولة أرشفة الرسالة الأولى
                try:
                    async for message in self.userbot.iter_messages(self.config.SOURCE_CHANNEL, limit=1):
                        await self.archive_message(message)
                        await update.message.reply_text(
                            f"✅ **نجح اختبار الأرشفة!**\n"
                            f"• تم أرشفة الرسالة `{message.id}` بنجاح\n"
                            f"• التاريخ: `{message.date.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                            f"• المحتوى: `{(message.text or message.caption or '[وسائط]')[:100]}`",
                            parse_mode='Markdown'
                        )
                        break
                except Exception as e:
                    await update.message.reply_text(f"❌ فشل اختبار الأرشفة: {e}")
            else:
                await update.message.reply_text(report, parse_mode='Markdown')
            
            # اختبار عدد الرسائل الإجمالي
            try:
                total_count = 0
                await update.message.reply_text("🔢 جاري حساب إجمالي الرسائل في القناة...")
                
                async for message in self.userbot.iter_messages(self.config.SOURCE_CHANNEL, limit=100):
                    total_count += 1
                
                await update.message.reply_text(
                    f"📊 **إحصائيات إضافية:**\n"
                    f"• تم العثور على `{total_count}` رسالة في آخر 100 رسالة\n"
                    f"• هذا يعني أن القناة تحتوي على رسائل قابلة للقراءة",
                    parse_mode='Markdown'
                )
            except Exception as e:
                await update.message.reply_text(f"⚠️ لا يمكن حساب إجمالي الرسائل: {e}")
        
        except Exception as e:
            await update.message.reply_text(
                f"❌ **فشل في الاتصال بالقناة:**\n"
                f"• القناة: `{self.config.SOURCE_CHANNEL}`\n"
                f"• الخطأ: `{str(e)}`\n\n"
                f"💡 **الحلول المقترحة:**\n"
                f"• تأكد من أن الـ Userbot عضو في القناة\n"
                f"• تأكد من صحة معرف القناة\n"
                f"• تأكد من صلاحيات القراءة\n"
                f"• جرب استخدام معرف رقمي بدلاً من @username",
                parse_mode='Markdown'
            )

    async def cmd_channel_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض معلومات مفصلة عن القناة"""
        if not self.is_admin(update.effective_user.id):
            return
        
        if not self.userbot or not self.userbot.is_connected():
            await update.message.reply_text("❌ Userbot غير متصل")
            return
        
        if not self.config.SOURCE_CHANNEL:
            await update.message.reply_text("❌ لم يتم تحديد القناة المصدر")
            return
        
        try:
            entity = await self.userbot.get_entity(self.config.SOURCE_CHANNEL)
            
            # جلب معلومات مفصلة
            info = f"""
📺 **معلومات القناة المفصلة:**

🏷️ **الأساسيات:**
• الاسم: `{entity.title}`
• المعرف الرقمي: `{entity.id}`
• المعرف النصي: `{getattr(entity, 'username', 'غير متوفر')}`
• النوع: `{type(entity).__name__}`

👥 **العضوية:**
• عدد الأعضاء: `{getattr(entity, 'participants_count', 'غير متوفر')}`
• تاريخ الإنشاء: `{getattr(entity, 'date', 'غير متوفر')}`

🔒 **الخصوصية:**
• قناة عامة: `{'نعم' if getattr(entity, 'username', None) else 'لا'}`
• محدودة: `{'نعم' if getattr(entity, 'restricted', False) else 'لا'}`
• محققة: `{'نعم' if getattr(entity, 'verified', False) else 'لا'}`

📝 **الوصف:**
{getattr(entity, 'about', 'لا يوجد وصف') or 'لا يوجد وصف'}
        """
            
            await update.message.reply_text(info, parse_mode='Markdown')
            
            # اختبار جلب رسائل من تواريخ مختلفة
            await update.message.reply_text("🔍 جاري اختبار جلب رسائل من تواريخ مختلفة...")
            
            date_tests = [
                datetime.now().date(),  # اليوم
                datetime.now().date() - timedelta(days=1),  # أمس
                datetime.now().date() - timedelta(days=7),  # قبل أسبوع
                datetime.now().date() - timedelta(days=30),  # قبل شهر
            ]
            
            results = []
            for test_date in date_tests:
                try:
                    count = 0
                    async for message in self.userbot.iter_messages(
                        self.config.SOURCE_CHANNEL,
                        offset_date=test_date + timedelta(days=1),
                        limit=10
                    ):
                        if message.date.date() == test_date:
                            count += 1
                    
                    results.append(f"• {test_date}: `{count}` رسالة")
                except Exception as e:
                    results.append(f"• {test_date}: ❌ خطأ - {e}")
            
            test_report = "📅 **اختبار الرسائل بالتاريخ:**\n" + "\n".join(results)
            await update.message.reply_text(test_report, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ في جلب معلومات القناة: {e}")

    def is_admin(self, user_id):
        """Checks if a user is an admin."""
        return str(user_id) in self.config.ADMIN_USER_IDS

    async def archive_message(self, message):
        """Archives a message to the specified chat."""
        if not self.config.ARCHIVE_CHAT:
            logger.warning("Archive chat is not set.")
            return

        try:
            if message.text:
                await self.userbot.send_message(self.config.ARCHIVE_CHAT, message.text)
            elif message.photo:
                await self.userbot.send_photo(self.config.ARCHIVE_CHAT, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await self.userbot.send_video(self.config.ARCHIVE_CHAT, message.video.file_id, caption=message.caption)
            else:
                logger.warning(f"Unsupported message type: {type(message)}")

            logger.info(f"Archived message {message.id} to {self.config.ARCHIVE_CHAT}")

        except Exception as e:
            logger.error(f"Failed to archive message {message.id}: {e}")

    async def process_channel_messages(self):
        """Processes messages from the source channel and archives them based on the keyword."""
        if not self.userbot or not self.userbot.is_connected():
            logger.error("Userbot is not connected.")
            return

        if not self.config.SOURCE_CHANNEL or not self.config.KEYWORD:
            logger.warning("Source channel or keyword is not set.")
            return

        try:
            async for message in self.userbot.iter_messages(self.config.SOURCE_CHANNEL, limit=5):
                if self.config.KEYWORD.lower() in message.text.lower():
                    await self.archive_message(message)
        except Exception as e:
            logger.error(f"Error processing channel messages: {e}")

    def start_bot(self):
        """Starts the Telegram bot."""
        self.job_queue.run_repeating(lambda context: self.process_channel_messages(), interval=60, first=5)
        self.application.run_polling()

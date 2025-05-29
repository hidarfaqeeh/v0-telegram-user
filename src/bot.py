import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramArchiveBot:
    def __init__(self, token, admin_ids):
        self.token = token
        self.admin_ids = admin_ids
        self.application = ApplicationBuilder().token(self.token).build()
        self.job_queue = self.application.job_queue
        self.channel_id = None  # Initialize channel_id

    def is_admin(self, user_id):
        return user_id in self.admin_ids

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Starts the bot."""
        if not self.is_admin(update.effective_user.id):
            return
        await context.bot.send_message(chat_id=update.effective_chat.id, text="أهلاً بك! البوت جاهز.")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة المحسن"""
        if not self.is_admin(update.effective_user.id):
            return
    
        help_text = """
🆘 **دليل استخدام البوت المحسن:**

**📁 أوامر الأرشفة:**
• `/archive_today` - أرشفة منشورات اليوم
• `/archive_day YYYY-MM-DD` - أرشفة يوم محدد
• `/archive_month YYYY-MM` - أرشفة شهر كامل
• `/archive_year YYYY` - أرشفة سنة كاملة
• `/archive_range تاريخ_البداية تاريخ_النهاية` - أرشفة نطاق مخصص
• `/archive_all` - أرشفة جميع المنشورات (تحذير!)

**📊 أوامر المعلومات:**
• `/status` - عرض إحصائيات الأرشيف
• `/browse` - تصفح الأرشيف تفاعلياً (محسن!)
• `/view_post message_id` - عرض منشور بالتفصيل

**🔍 البحث:**
• `/search كلمة البحث` - البحث في المحتوى

**⚙️ الإدارة:**
• `/set_channel @channel` - تحديد القناة المصدر
• `/export YYYY-MM-DD` - تصدير أرشيف يوم
• `/diagnostics` - تشخيص مشاكل البوت

**✨ الميزات الجديدة:**
• 🖼️ عرض الوسائط (صور، فيديوهات، ملفات)
• ⏭️ التنقل بين المنشورات (السابق/التالي)
• 📊 إحصائيات مفصلة لكل منشور
• 🔄 أرشفة نطاقات زمنية كبيرة
• 💾 حفظ محسن مع معلومات إضافية

**💡 نصائح:**
- استخدم الأزرار التفاعلية للتنقل السهل
- الأرشفة التلقائية تعمل في الخلفية
- يمكن عرض الوسائط مع النصوص
- التنقل بين المنشورات سهل وسريع

**🔗 روابط مفيدة:**
- احصل على API من: https://my.telegram.org/apps
- أنشئ بوت جديد: @BotFather
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def set_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sets the source channel for archiving."""
        if not self.is_admin(update.effective_user.id):
            return

        try:
            channel_username = context.args[0]
            # Basic validation for channel username format
            if not channel_username.startswith('@'):
                await update.message.reply_text("تنسيق اسم القناة غير صحيح. يجب أن يبدأ بـ @.")
                return

            # Resolve channel ID (this might require the bot to be an admin in the channel)
            try:
                chat = await context.bot.get_chat(channel_username)
                self.channel_id = chat.id
                await update.message.reply_text(f"تم تعيين القناة المصدر إلى: {channel_username} (ID: {self.channel_id})")
            except Exception as e:
                await update.message.reply_text(f"فشل في الحصول على معلومات القناة. تأكد من أن البوت عضو في القناة و لديه صلاحيات كافية. الخطأ: {e}")
                return

        except (IndexError, ValueError):
            await update.message.reply_text("الرجاء تحديد اسم القناة (مثال: `/set_channel @اسم_القناة`).")

    def add_handlers(self):
        """Adds command handlers to the bot."""
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('help', self.cmd_help))
        self.application.add_handler(CommandHandler('set_channel', self.set_channel))

    def run(self):
        """Runs the bot."""
        self.add_handlers()
        self.application.run_polling()

if __name__ == '__main__':
    # Replace with your actual bot token and admin user IDs
    bot_token = "YOUR_BOT_TOKEN"
    admin_user_ids = [123456789]  # Replace with actual admin user IDs

    bot = TelegramBot(bot_token, admin_user_ids)
    bot.run()

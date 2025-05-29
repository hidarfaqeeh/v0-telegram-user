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
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            finally:
                await self.bot_app.updater.stop()
                await self.bot_app.stop()

import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from yt_dlp import YoutubeDL

# إعدادات البوت
TOKEN1 = "7818215743:AAFh-QLHNx9mnZnnosJmsEarSpCKRgJ18Do"
TOKEN2 = "8059875744"
PORT = int(os.environ.get('PORT', 5000))
ALLOWED_USERS = []  # أضف أي دي المستخدمين المسموح لهم

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# معالجة الأمر /start
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        f"مرحباً {user.mention_markdown_v2()}\!\n"
        "أرسل لي رابط فيديو من:\n"
        "- إنستغرام\n- فيسبوك\n- تيك توك\n- يوتيوب\n- تويتر\n"
        "وسأحاول تحميله وإرساله لك"
    )

# معالجة الروابط المرسلة
def handle_url(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        update.message.reply_text("⚠️ ليس لديك صلاحية استخدام هذا البوت")
        return
    
    url = update.message.text
    chat_id = update.message.chat_id
    
    try:
        update.message.reply_text("⏳ جاري التحميل...")
        
        # خيارات التنزيل
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
                {'key': 'EmbedThumbnail'}
            ],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # إرسال الفيديو
            with open(filename, 'rb') as video_file:
                context.bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption=f"✅ {info['title']}\n\n@VideoDownloaderBot",
                    supports_streaming=True
                )
            
            # حذف الملفات المؤقتة
            os.remove(filename)
            if os.path.exists(filename + '.webp'):
                os.remove(filename + '.webp')
    
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text(f"❌ فشل التحميل: {str(e)}")

# تشغيل البوتات
def main() -> None:
    # قائمة بالتوكنات
    tokens = [TOKEN1, TOKEN2]
    updaters = []
    
    for i, token in enumerate(tokens):
        try:
            updater = Updater(token, use_context=True)
            dispatcher = updater.dispatcher

            # معالجات الأوامر
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_url))
            
            # إذا كنا في Replit والبوت الأول (i==0) نستخدم ويب هوك، والباقي polling
            if i == 0 and 'REPLIT' in os.environ:
                # البوت الأول: ويب هوك
                updater.start_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    url_path=token,
                    webhook_url=f"https://{os.environ['REPL_SLUG']}.{os.environ['REPL_OWNER']}.repl.co/{token}"
                )
                logger.info(f"Bot {i+1} started with webhook")
            else:
                # البوت الثاني: polling (أو إذا لم نكن في Replit)
                updater.start_polling()
                logger.info(f"Bot {i+1} started with polling")
            
            updaters.append(updater)
        except Exception as e:
            logger.error(f"Failed to start bot {i+1}: {e}")

    # انتظر حتى يتم إيقاف جميع البوتات
    for updater in updaters:
        updater.idle()

if __name__ == '__main__':
    main()

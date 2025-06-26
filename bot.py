import os
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("About Me 👤", url="https://t.me/ZH14UI")]]
    await update.message.reply_text(
        "🎬 Send me a video and I will convert it to a GIF for you — automatically!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("⚠️ Please send a valid video.")
        return

    user_id = update.effective_user.id
    video_path = f"video_{user_id}.mp4"
    gif_path = f"gif_{user_id}.gif"

    await update.message.reply_text("⏳ Processing your GIF...")

    try:
        file = await context.bot.get_file(video.file_id)
        await file.download_to_drive(video_path)

        clip = VideoFileClip(video_path)
        clip.write_gif(gif_path, program="ffmpeg")

        await context.bot.send_document(chat_id=user_id, document=open(gif_path, 'rb'), caption="✅ Done! Here's your GIF.")
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Error: {e}")
    finally:
        for f in [video_path, gif_path]:
            if os.path.exists(f):
                os.remove(f)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    print("🤖 Bot is running (no text overlay)...")
    app.run_polling()

if __name__ == "__main__":
    main()

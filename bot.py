import os
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Save user session info in memory
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("About Me 👤", url="https://t.me/ZH14UI")]
    ]
    await update.message.reply_text(
        "🎬 Send a video ➜ send overlay text ➜ choose font size ➜ get your GIF!\nSupports Khmer & English ✅",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("⚠️ Please send a valid video.")
        return

    file = await context.bot.get_file(video.file_id)
    video_path = f"video_{user_id}.mp4"
    await file.download_to_drive(video_path)

    user_settings[user_id] = {'video_path': video_path}
    await update.message.reply_text("📝 Great! Now send the text to overlay (Khmer or English).")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_settings or 'video_path' not in user_settings[user_id]:
        await update.message.reply_text("⚠️ Please send a video first.")
        return

    user_settings[user_id]['text'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Size 50", callback_data="size_50")],
        [InlineKeyboardButton("Size 100", callback_data="size_100")],
        [InlineKeyboardButton("Size 150", callback_data="size_150")],
    ]
    await update.message.reply_text("🔠 Choose your font size:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    settings = user_settings.get(user_id)
    if not settings:
        await query.edit_message_text("⚠️ Session expired. Please start again.")
        return

    size = int(query.data.split("_")[1])
    video_path = settings['video_path']
    text = settings['text']
    gif_path = f"gif_{user_id}.gif"
    font_path = "KhmerOSNew-Bold"  # Ensure this file exists in your project folder

    await query.edit_message_text("⏳ Creating your GIF... Please wait...")

    try:
        clip = VideoFileClip(video_path)

        # Create styled outlined text
        txt = TextClip(
            text,
            fontsize=size,
            font=font_path,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption"
        ).set_pos("center").set_duration(clip.duration)

        result = CompositeVideoClip([clip, txt])
        result.write_gif(gif_path, program="ffmpeg")

        await context.bot.send_document(chat_id=user_id, document=open(gif_path, 'rb'), caption="✅ Here is your GIF!")
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Error: {e}")
    finally:
        for file in [video_path, gif_path]:
            if os.path.exists(file):
                os.remove(file)
        user_settings.pop(user_id, None)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_size_selection))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

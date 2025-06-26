import os
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Global cache for user settings
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("About Me 👤", url="https://t.me/ZH14UI")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎬 Send me a Telegram video and I will convert it to GIF with custom text.\n\nSteps:\n1. Send a video\n2. I will ask for your text\n3. Then select size\nDone ✅",
        reply_markup=reply_markup
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    video = update.message.video or update.message.document

    if not video:
        await update.message.reply_text("❗ Please send a Telegram video.")
        return

    file = await context.bot.get_file(video.file_id)
    video_path = f"input_{user_id}.mp4"
    await file.download_to_drive(video_path)

    user_settings[user_id] = {'video_path': video_path}
    await update.message.reply_text("📝 Now send the text to overlay (Khmer or English).")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_settings or 'video_path' not in user_settings[user_id]:
        await update.message.reply_text("⚠️ Please send a video first.")
        return

    user_settings[user_id]['text'] = update.message.text

    # Ask for text size
    keyboard = [
        [InlineKeyboardButton("Text Size: 50", callback_data='size_50')],
        [InlineKeyboardButton("Text Size: 100", callback_data='size_100')],
        [InlineKeyboardButton("Text Size: 150", callback_data='size_150')],
    ]
    await update.message.reply_text("🔠 Choose the font size:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_settings:
        await query.edit_message_text("⚠️ Session expired. Please start over by sending a video.")
        return

    size = int(query.data.split('_')[1])
    settings = user_settings[user_id]
    video_path = settings['video_path']
    text = settings['text']
    gif_path = f"output_{user_id}.gif"

    await query.edit_message_text("⏳ Converting to GIF... Please wait...")

    try:
        clip = VideoFileClip(video_path)
        txt_clip = TextClip(text, fontsize=size, color='white', font='KhmerOSNew-Bold.')\
                    .set_position('center').set_duration(clip.duration)
        final = CompositeVideoClip([clip, txt_clip])
        final.write_gif(gif_path, program='ffmpeg')

        await context.bot.send_document(chat_id=user_id, document=open(gif_path, 'rb'), caption="🎉 Here is your GIF!")

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Error: {str(e)}")

    finally:
        os.remove(video_path)
        if os.path.exists(gif_path):
            os.remove(gif_path)
        user_settings.pop(user_id, None)

# Main application setup
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_size_selection))

if __name__ == '__main__':
    print("🤖 Bot is running...")
    app.run_polling()

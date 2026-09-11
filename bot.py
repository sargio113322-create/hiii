import os
import re
import logging
import tempfile
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Render-এ চালানোর জন্য লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# আপনার টেলিগ্রাম বট টোকেন Render-এর Environment Variable থেকে আসবে
TOKEN = os.environ.get("8922780779:AAHApcDnlKgn9Gb_S9cViIqDOp56EDYSlHE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """বট শুরু হলে /start কমান্ডে সাড়া দেবে।"""
    await update.message.reply_text(
        "🎵 হ্যালো! আমাকে একটি ইউটিউব ভিডিওর লিংক পাঠান, আমি MP3 বানিয়ে দেব।"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ইউজারের পাঠানো মেসেজ থেকে ইউটিউব লিংক খুঁজে বের করে প্রসেস করবে।"""
    url = update.message.text

    # লিংকটি ইউটিউবের কিনা তা সাধারণ রেগুলার এক্সপ্রেশন দিয়ে চেক করা
    if not re.search(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/', url):
        await update.message.reply_text("❌ দয়া করে সঠিক ইউটিউব লিংক পাঠান।")
        return

    # ইউজারকে জানানো যে প্রসেস শুরু হয়েছে
    processing_msg = await update.message.reply_text("⏳ অডিও ডাউনলোড এবং কনভার্ট করা হচ্ছে...")

    # টেম্পোরারি ডিরেক্টরি তৈরি (Render-এ এফেমেরাল, তাই শেষে ডিলিট করে দেওয়া হবে)
    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = str(Path(temp_dir) / "%(title)s.%(ext)s")

        # yt-dlp কমান্ড: শুধু অডিও ডাউনলোড করে MP3 ফরম্যাটে কনভার্ট করবে
        command = [
            "yt-dlp",
            "-x",                     # অডিও এক্সট্রাক্ট
            "--audio-format", "mp3",  # MP3 ফরম্যাট
            "--audio-quality", "0",   # সেরা অডিও কোয়ালিটি
            "-o", output_template,    # আউটপুট ফাইলের নাম
            url
        ]

        try:
            # সাবপ্রসেস দিয়ে yt-dlp চালানো
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"yt-dlp error: {result.stderr}")
                await processing_msg.edit_text("❌ ভিডিওটি ডাউনলোড করা যায়নি। লিংকটি চেক করুন।")
                return

            # টেম্পোরারি ডিরেক্টরি থেকে তৈরি হওয়া MP3 ফাইলটি খুঁজে বের করা
            mp3_files = list(Path(temp_dir).glob("*.mp3"))
            if not mp3_files:
                await processing_msg.edit_text("❌ MP3 ফাইল তৈরি করতে সমস্যা হয়েছে।")
                return

            mp3_path = mp3_files[0]

            # ফাইলটি ইউজারকে পাঠানো (send_audio ব্যবহার করে)
            await processing_msg.edit_text("📤 ফাইল পাঠানো হচ্ছে...")
            with open(mp3_path, "rb") as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=mp3_path.stem,
                    performer="YouTube"
                )

            # সফল মেসেজ ডিলিট করা (ইউজার ইন্টারফেস পরিষ্কার রাখতে)
            await processing_msg.delete()

        except subprocess.TimeoutExpired:
            await processing_msg.edit_text("⏰ সময় শেষ! ভিডিওটি হয়তো অনেক বড়।")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await processing_msg.edit_text("❌ একটি অপ্রত্যাশিত সমস্যা হয়েছে।")

def main() -> None:
    """বট চালু করে এবং টেলিগ্রামের সাথে কানেক্ট করে।"""
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable missing!")

    # Application তৈরি
    application = Application.builder().token(TOKEN).build()

    # হ্যান্ডলার যুক্ত করা
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # বট চালু (Render-এ Webhook এর বদলে Polling ব্যবহার করা হচ্ছে, কারণ এটা সহজ এবং নির্ভরযোগ্য)
    # Render-এর ফ্রি ইনস্ট্যান্স ঘুমিয়ে পড়লেও, পুনরায় জাগলে এটি আবার কাজ করবে।
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

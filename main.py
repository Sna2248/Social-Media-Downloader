#!/usr/bin/env python3
"""
Social Media Downloader Telegram Bot
Supports: YouTube, Instagram, TikTok, Twitter/X, Facebook, and more
Uses yt-dlp for downloading
"""

import os
import re
import asyncio
import logging
import tempfile
import shutil
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatAction
import yt_dlp

# ── Configuration ──────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MAX_FILE_SIZE_MB = 250          # Telegram bot limit is 250 MB
DOWNLOAD_DIR = tempfile.mkdtemp()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── URL Detection ──────────────────────────────────────────────────────────────
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "instagram.com",
    "tiktok.com",
    "twitter.com", "x.com",
    "facebook.com", "fb.watch",
    "vimeo.com",
    "reddit.com",
    "twitch.tv",
    "dailymotion.com",
    "pinterest.com",
    "snapchat.com",
    "threads.net",
    "linkedin.com",
]

URL_REGEX = re.compile(
    r"https?://(?:www\.)?[^\s]+"
)


def extract_url(text: str) -> str | None:
    """Extract first URL from text."""
    match = URL_REGEX.search(text)
    return match.group(0) if match else None


def is_supported_url(url: str) -> bool:
    return any(domain in url for domain in SUPPORTED_DOMAINS)


# ── Download Helpers ───────────────────────────────────────────────────────────
def get_ydl_opts(output_path: str, format_type: str = "video") -> dict:
    """Build yt-dlp options."""
    base_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
    }

    if format_type == "audio":
        base_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    elif format_type == "video":
        # Best video + audio, max ~720p to stay within Telegram limits
        base_opts["format"] = (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
            "/bestvideo[height<=720]+bestaudio"
            "/best[height<=720]"
            "/best"
        )
        base_opts["merge_output_format"] = "mp4"
    elif format_type == "thumbnail":
        base_opts["skip_download"] = True
        base_opts["writethumbnail"] = True

    return base_opts


async def fetch_info(url: str) -> dict | None:
    """Fetch media info without downloading."""
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noplaylist": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        logger.error(f"Info fetch error: {e}")
        return None


async def download_media(url: str, format_type: str, tmp_dir: str) -> tuple[str | None, str | None]:
    """Download media, return (filepath, error_message)."""
    output_template = os.path.join(tmp_dir, "%(title).50s.%(ext)s")
    opts = get_ydl_opts(output_template, format_type)

    try:
        loop = asyncio.get_event_loop()

        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

        await loop.run_in_executor(None, _download)

        # Find downloaded file
        files = list(Path(tmp_dir).iterdir())
        if not files:
            return None, "No file was downloaded."

        file_path = str(files[0])
        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            return None, f"❌ File too large ({size_mb:.1f} MB). Telegram limit is {MAX_FILE_SIZE_MB} MB."

        return file_path, None

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private" in msg or "login" in msg.lower():
            return None, "❌ This content is private or requires login."
        if "not available" in msg.lower():
            return None, "❌ Content not available in your region or has been removed."
        return None, f"❌ Download failed: {msg[:200]}"
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None, f"❌ Unexpected error: {str(e)[:200]}"


# ── Command Handlers ───────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Welcome to Social Media Downloader Bot!*\n\n"
        "Simply send me a link from:\n"
        "• 📺 YouTube\n"
        "• 📸 Instagram\n"
        "• 🎵 TikTok\n"
        "• 🐦 Twitter / X\n"
        "• 👥 Facebook\n"
        "• 🎬 Vimeo, Reddit, Twitch & more\n\n"
        "Only Video, Audio, and Thumbnails are supported.\n"
        "I'll ask what format you want, then send the file!\n\n"
        "Commands:\n"
        "/start – Show this message\n"
        "/help – How to use\n"
        "/supported – List supported sites\n\n"
        "Creator: @Veasna600"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *How to use:*\n\n"
        "1. Paste or send a social media URL\n"
        "2. Choose download format (Video / Audio / Photo)\n"
        "3. Wait while I download & send the file\n\n"
        "⚠️ *Limits:*\n"
        "• Max file size: 250 MB (Telegram limit)\n"
        "• Videos capped at 720p to stay within limit\n"
        "• Private / age-restricted content may fail\n\n"
        "💡 *Tip:* Works with playlists too – I'll grab the first item.\n\n"
        "Creator: @Veasna600"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def supported_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sites = "\n".join(f"• {d}" for d in SUPPORTED_DOMAINS)
    await update.message.reply_text(
        f"✅ *Supported domains:*\n\n{sites}\n\n"
        "_(yt-dlp supports 1000+ sites – send any URL and I'll try!)_",
        parse_mode=ParseMode.MARKDOWN,
    )


# ── URL Message Handler ────────────────────────────────────────────────────────
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = extract_url(update.message.text)
    if not url:
        await update.message.reply_text("⚠️ Please send a valid URL.")
        return

    # Store URL in user context
    context.user_data["url"] = url

    # Fetch info
    status_msg = await update.message.reply_text("🔍 Fetching media info…")
    info = await fetch_info(url)

    if not info:
        await status_msg.edit_text(
            "❌ Could not fetch info from this URL.\n"
            "Make sure it's a public, supported link."
        )
        return

    title = info.get("title", "Unknown title")[:60]
    uploader = info.get("uploader", "Unknown")
    duration = info.get("duration")
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "N/A"

    # Build format keyboard
    keyboard = [
        [
            InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio"),
        ],
        [InlineKeyboardButton("🖼 Thumbnail", callback_data="dl_thumbnail")],
        [InlineKeyboardButton("❌ Cancel", callback_data="dl_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"📌 *{title}*\n"
        f"👤 {uploader}\n"
        f"⏱ {duration_str}\n\n"
        "Choose download format:"
    )
    await status_msg.edit_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


# ── Callback Handler ───────────────────────────────────────────────────────────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    url = context.user_data.get("url")

    if data == "dl_cancel" or not url:
        await query.edit_message_text("❌ Cancelled.")
        return

    format_map = {
        "dl_video": "video",
        "dl_audio": "audio",
        "dl_thumbnail": "thumbnail",
    }
    fmt = format_map.get(data, "video")
    fmt_label = {"video": "🎬 Video", "audio": "🎵 Audio", "thumbnail": "🖼 Thumbnail"}[fmt]

    await query.edit_message_text(f"⬇️ Downloading {fmt_label}…\nThis may take a moment.")

    # Send typing action
    await context.bot.send_chat_action(
        chat_id=query.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT
    )

    tmp_dir = tempfile.mkdtemp(dir=DOWNLOAD_DIR)
    try:
        file_path, error = await download_media(url, fmt, tmp_dir)

        if error:
            await query.edit_message_text(error)
            return

        await query.edit_message_text("📤 Uploading to Telegram…")

        ext = Path(file_path).suffix.lower()

        with open(file_path, "rb") as f:
            if fmt == "audio" or ext == ".mp3":
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=f,
                    caption="🎵 Downloaded via @Chatbot_KiloPro_BOT",
                )
            elif fmt == "thumbnail" or ext in (".jpg", ".jpeg", ".png", ".webp"):
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=f,
                    caption="🖼 Thumbnail downloaded",
                )
            else:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=f,
                    caption="🎬 Downloaded via Social Media Downloader Bot",
                    supports_streaming=True,
                )

        await query.edit_message_text("✅ Done! Enjoy your media.")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Non-URL text ───────────────────────────────────────────────────────────────
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please send me a social media URL to download.\n"
        "Type /help for instructions."
    )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Set your BOT_TOKEN in the environment or edit bot.py")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("supported", supported_cmd))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"https?://"), handle_url))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^dl_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot is running… Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

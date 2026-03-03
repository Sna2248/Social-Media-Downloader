# Social Media Downloader

Enjoy :)

# 📥 Social Media Downloader Telegram Bot

A powerful Telegram bot that downloads videos, audio, and images from 1000+ social media platforms using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## ✅ Supported Platforms

- YouTube
- Instagram (public posts/reels)
- TikTok
- Twitter / X
- Facebook
- Reddit
- Vimeo
- Twitch
- Dailymotion
- Pinterest
- Threads
- LinkedIn
- ...and 1000+ more via yt-dlp

---

## 🚀 Setup

### 1. Prerequisites

- Python 3.11+
- `ffmpeg` installed on your system

Install ffmpeg:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows – download from https://ffmpeg.org/download.html
```

### 2. Get a Bot Token

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy your **BOT_TOKEN**

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
export BOT_TOKEN="your_token_here"
python bot.py
```

Or on Windows:

```cmd
set BOT_TOKEN=your_token_here
python bot.py
```

---

## 🐳 Docker (Optional)

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY bot.py .
CMD ["python", "bot.py"]
```

Build & run:

```bash
docker build -t social-dl-bot .
docker run -e BOT_TOKEN=your_token_here social-dl-bot
```

---

## 💬 Bot Commands

| Command      | Description            |
| ------------ | ---------------------- |
| `/start`     | Welcome message        |
| `/help`      | Usage instructions     |
| `/supported` | List supported domains |

**Usage:** Just paste any social media URL and the bot will:

1. Fetch media info (title, uploader, duration)
2. Ask your preferred format (Video / Audio / Thumbnail)
3. Download and send the file directly in Telegram

---

## ⚠️ Limitations

- Telegram bots can only send files up to **50 MB**
- Videos are capped at **720p** to stay within limits
- Private / login-required content won't work
- Instagram may require cookies for some content

## 🍪 Instagram / Private Content (Advanced)

Export your browser cookies to a `cookies.txt` file and add to yt-dlp options:

```python
opts["cookiefile"] = "cookies.txt"
```

---

## 📜 License

MIT – use freely, but respect platform Terms of Service.

Creator: Mario

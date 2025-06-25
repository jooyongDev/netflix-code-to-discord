# 📬 Netflix Code to Discord

This script automatically checks your Naver email inbox for new Netflix verification emails, extracts any code link, and sends it to a Discord channel using a webhook.

## 🔧 Features

- IMAP polling every 30 seconds
- Filters emails from `info@account.netflix.com` within the last 1 hour
- Extracts code URLs containing keywords like `코드` or `code`
- Sends the link to a configured Discord webhook
- Prevents duplicate notifications using UID tracking

## ⚙️ Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your `.env` file:**

   Create a `.env` file in the root directory with the following:

   ```env
   EMAIL=your_naver_email@naver.com
   PASSWORD=your_app_password
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
   ```

   > 🔐 Make sure to use an [app password](https://help.naver.com/) for Naver if 2FA is enabled.

3. **Run the script:**

   ```bash
   python main.py
   ```

## 📁 File Overview

- `main.py`: The main listener and processing script.
- `.env`: Holds your secrets (not committed).
- `processed_uids.json`: Stores already-handled email UIDs.
- `requirements.txt`: Python dependencies.
- `.gitignore`: Prevents secrets and virtualenv from being committed.

## ✅ Requirements

- Python 3.8+
- Naver email with IMAP enabled
- Discord server with a webhook created

## 🛡️ Security

- This script disables SSL certificate verification for IMAP (for now). For production use, please **re-enable SSL checks**.

## 📄 License

MIT License

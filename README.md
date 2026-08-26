# 🛒 Blox Fruits Shop Bot (Python)

Discord bot for a Blox Fruits **buy & sell** server. Built with **discord.py** — made to run on a **Python** hosting panel (like your Pterodactyl `python app.py` server).

## ✅ Why this version
Your panel runs **Python** and looks for **`app.py`** + **`requirements.txt`**. This project provides exactly that, so it runs on your current server with no egg change.

## ✨ Features
- 🎫 Dropdown ticket panel (Buy / Sell / Middleman)
- ✋ Claim button, 🔒 close-with-confirmation, 📄 auto-transcript (to log channel + DM)
- 🏷️ `/stock` and `/price` (live, editable in `config.py`)
- 🔧 `/setstock` for staff, saved to disk
- ⭐ `/vouch` + `/vouches` review system

## 📁 Files
| File | What it is |
|------|-----------|
| `app.py` | The bot. Panel runs this. Don't edit. |
| `config.py` | **Edit this** — IDs, prices, ticket types, payment methods. |
| `store.py` | Saves stock/vouches to `data.json`. |
| `requirements.txt` | Dependencies the panel installs automatically. |
| `.env` | Your token + guild ID (already filled in). |

---

## 🚀 How to run on your Pterodactyl / Python panel

1. Go to **Files** in your panel and upload these files into `/home/container`:
   - `app.py`, `config.py`, `store.py`, `requirements.txt`
   - (Do **not** upload `__pycache__` or `data.json`.)

2. Set your token. **Two options:**
   - **Easiest:** In the panel go to **Startup** and add a variable / or edit `.env` so `DISCORD_TOKEN` and `GUILD_ID` are set. Uploading the included `.env` works too.
   - Many Python eggs have a **"Python Packages"** field — leave it, `requirements.txt` handles it.

3. Make sure the panel's startup uses:
   - **App file / Python file:** `app.py`
   - **Requirements file:** `requirements.txt` (so it runs `pip install -r requirements.txt`)

4. Click **Start**. When the console prints:
   ```
   ✅ Synced 7 slash commands.
   ✅ Logged in as ...
   ```
   the bot is live. Commands appear in your server instantly.

5. In Discord, run **`/panel`** (staff only) in the channel where you want the ticket menu.

> Note: discord.py **auto-syncs** the slash commands on startup — there's no separate "deploy" step like the Node version.

---

## 💬 Commands
| Command | Who | Does |
|---------|-----|------|
| `/panel` | Staff | Posts the ticket dropdown panel |
| `/stock` | Everyone | Shows all fruits, prices, stock |
| `/price <fruit>` | Everyone | One fruit's price & stock |
| `/setstock <fruit> <amount>` | Staff | Update stock (saved) |
| `/vouch <stars> <comment>` | Everyone | Leave a review |
| `/vouches` | Everyone | Total vouches & average |
| `/close` | Staff | Close current ticket |

## 🔧 Requirements for the bot to work
- **Message Content Intent** ON (Developer Portal → Bot).
- Bot invited with **Manage Channels, Manage Roles, Send Messages, Embed Links, Read Message History, Attach Files**.
- The bot's role sits **above** the staff role.

## 🔐 Security — IMPORTANT
Your token was shared in plain text during setup. Please **reset it** (Developer Portal → Bot → Reset Token) and update `DISCORD_TOKEN` in `.env`. Never upload `.env` to GitHub (`.gitignore` blocks it).

## ❓ If it still crashes on the panel
- `can't open file 'app.py'` → files must be in `/home/container`, not a subfolder.
- `No module named discord` → the Requirements file isn't set to `requirements.txt`, or reinstall from console: `pip install -r requirements.txt`.
- `PrivilegedIntentsRequired` → turn on Message Content Intent.

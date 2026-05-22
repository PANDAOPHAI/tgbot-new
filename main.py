from telethon import TelegramClient, events
from flask import Flask, render_template, request, redirect
import threading
import requests
import re
import os
import time
import asyncio

# ====================================
# FLASK SERVER
# ====================================

app = Flask(__name__)

# ====================================
# TELEGRAM API
# ====================================

api_id = 21836257
api_hash = "817ab8acbb95ae9ad02b74bd83ccbea2"

# ====================================
# TMDB API
# ====================================

TMDB_API_KEY = "f1e46d83ecce5dc29c90d9d2ed41f2ed"

# ====================================
# SOURCE CHANNELS
# ====================================

SOURCE_IDS = [
    -1003900368405,
    -1003682968695
]

# ====================================
# TARGET CHANNELS
# ====================================

TARGET_IDS = [
    -1003927415038,
    -1002444484223
]

# ====================================
# ADMIN / LOG CHANNEL
# ====================================

ADMIN_CHANNEL_ID = -1003999952586
LOG_CHANNEL_ID = -1003999952586

# ====================================
# CLIENT
# ====================================

client = TelegramClient(
    "session",
    api_id,
    api_hash
)

# ====================================
# STATS
# ====================================

stats = {
    "sent": 0,
    "skipped": 0,
    "errors": 0,
    "duplicates": 0
}

# ====================================
# CACHE / LOGS
# ====================================

sent_cache = set()
paused_targets = set()
recent_logs = []

# ====================================
# START TIME
# ====================================

start_time = time.time()

# ====================================
# SEND LOG
# ====================================

async def send_log(message):

    try:

        await client.send_message(
            LOG_CHANNEL_ID,
            message
        )

    except Exception as e:

        print("LOG ERROR:", e)

# ====================================
# ADD RECENT LOG
# ====================================

async def add_recent_log(text):

    recent_logs.append(text)

    if len(recent_logs) > 20:
        recent_logs.pop(0)

# ====================================
# GET UPTIME
# ====================================

def get_uptime():

    seconds = int(
        time.time() - start_time
    )

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours}h {minutes}m {secs}s"

# ====================================
# DASHBOARD
# ====================================

@app.route('/')
def dashboard():

    return render_template(
        "dashboard.html",

        sources=len(SOURCE_IDS),
        targets=len(TARGET_IDS),

        sent=stats["sent"],
        errors=stats["errors"],
        duplicates=stats["duplicates"],

        source_ids=SOURCE_IDS,
        target_ids=TARGET_IDS,
        paused_targets=paused_targets,

        logs=recent_logs[-10:]
    )

# ====================================
# DASHBOARD ADD SOURCE
# ====================================

@app.route('/addsource', methods=["POST"])
def add_source():

    try:

        source_id = int(
            request.form.get("source_id")
        )

        if source_id not in SOURCE_IDS:

            SOURCE_IDS.append(source_id)

            msg = f"📡 SOURCE ADDED → {source_id}"

            recent_logs.append(msg)

            asyncio.run_coroutine_threadsafe(
                send_log(msg),
                client.loop
            )

    except Exception as e:

        recent_logs.append(
            f"❌ SOURCE ERROR → {e}"
        )

    return redirect("/")

# ====================================
# DASHBOARD REMOVE SOURCE
# ====================================

@app.route('/removesource', methods=["POST"])
def remove_source():

    try:

        source_id = int(
            request.form.get("source_id")
        )

        if source_id in SOURCE_IDS:

            SOURCE_IDS.remove(source_id)

            msg = f"🗑 SOURCE REMOVED → {source_id}"

            recent_logs.append(msg)

            asyncio.run_coroutine_threadsafe(
                send_log(msg),
                client.loop
            )

    except Exception as e:

        recent_logs.append(
            f"❌ REMOVE SOURCE ERROR → {e}"
        )

    return redirect("/")

# ====================================
# DASHBOARD ADD TARGET
# ====================================

@app.route('/addtarget', methods=["POST"])
def add_target():

    try:

        target_id = int(
            request.form.get("target_id")
        )

        if target_id not in TARGET_IDS:

            TARGET_IDS.append(target_id)

            msg = f"🎯 TARGET ADDED → {target_id}"

            recent_logs.append(msg)

            asyncio.run_coroutine_threadsafe(
                send_log(msg),
                client.loop
            )

    except Exception as e:

        recent_logs.append(
            f"❌ TARGET ERROR → {e}"
        )

    return redirect("/")

# ====================================
# DASHBOARD REMOVE TARGET
# ====================================

@app.route('/removetarget', methods=["POST"])
def remove_target():

    try:

        target_id = int(
            request.form.get("target_id")
        )

        if target_id in TARGET_IDS:

            TARGET_IDS.remove(target_id)

            msg = f"🗑 TARGET REMOVED → {target_id}"

            recent_logs.append(msg)

            asyncio.run_coroutine_threadsafe(
                send_log(msg),
                client.loop
            )

    except Exception as e:

        recent_logs.append(
            f"❌ REMOVE TARGET ERROR → {e}"
        )

    return redirect("/")

# ====================================
# DASHBOARD PAUSE TARGET
# ====================================

@app.route('/pause', methods=["POST"])
def pause_target():

    try:

        target_id = int(
            request.form.get("target_id")
        )

        paused_targets.add(target_id)

        msg = f"⏸ TARGET PAUSED → {target_id}"

        recent_logs.append(msg)

        asyncio.run_coroutine_threadsafe(
            send_log(msg),
            client.loop
        )

    except Exception as e:

        recent_logs.append(
            f"❌ PAUSE ERROR → {e}"
        )

    return redirect("/")

# ====================================
# DASHBOARD UNPAUSE TARGET
# ====================================

@app.route('/unpause', methods=["POST"])
def unpause_target():

    try:

        target_id = int(
            request.form.get("target_id")
        )

        if target_id in paused_targets:

            paused_targets.remove(target_id)

            msg = f"🟢 TARGET UNPAUSED → {target_id}"

            recent_logs.append(msg)

            asyncio.run_coroutine_threadsafe(
                send_log(msg),
                client.loop
            )

    except Exception as e:

        recent_logs.append(
            f"❌ UNPAUSE ERROR → {e}"
        )

    return redirect("/")

# ====================================
# DASHBOARD TEST
# ====================================

@app.route('/test')
def dashboard_test():

    async def send_test():

        test_caption = '''
╭──────────────⭓
┃ 🎬 TGFLIX TEST POST
╰──────────────⭓

✨ Dashboard Working Perfectly

━━━━━━━━━━━━━━━
🔥 Powered By TGFLIX
━━━━━━━━━━━━━━━
'''

        for target in TARGET_IDS:

            try:

                await client.send_message(
                    target,
                    test_caption
                )

            except:
                pass

    asyncio.run_coroutine_threadsafe(
        send_test(),
        client.loop
    )

    msg = "🧪 DASHBOARD TEST SENT"

    recent_logs.append(msg)

    asyncio.run_coroutine_threadsafe(
        send_log(msg),
        client.loop
    )

    return redirect("/")

# ====================================
# DASHBOARD BROADCAST
# ====================================

@app.route('/broadcast', methods=["POST"])
def dashboard_broadcast():

    try:

        message = request.form.get("message")

        async def send_broadcast():

            for target in TARGET_IDS:

                if target in paused_targets:
                    continue

                try:

                    await client.send_message(
                        target,
                        message
                    )

                except:
                    pass

        asyncio.run_coroutine_threadsafe(
            send_broadcast(),
            client.loop
        )

        msg = f"📢 DASHBOARD BROADCAST → {message}"

        recent_logs.append(msg)

        asyncio.run_coroutine_threadsafe(
            send_log(msg),
            client.loop
        )

    except Exception as e:

        recent_logs.append(
            f"❌ BROADCAST ERROR → {e}"
        )

    return redirect("/")

# ====================================
# RUN WEB
# ====================================

def run_web():

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )

# ====================================
# GET URL
# ====================================

def get_url(text):

    match = re.search(
        r'https?://\S+',
        text
    )

    if match:
        return match.group(0)

    return None

# ====================================
# NEWS CHECK
# ====================================

def is_news_post(text):

    news_keywords = [
        "officially announced",
        "release date",
        "coming soon",
        "set to release",
        "announced"
    ]

    text = text.lower()

    for word in news_keywords:

        if word in text:
            return True

    return False

# ====================================
# MOVIE CHECK
# ====================================

def is_movie(text):

    return "movie" in text.lower()

# ====================================
# GET SEASON
# ====================================

def get_season(text):

    match = re.search(
        r'Season\s*(\d+)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None

# ====================================
# GET EPISODE
# ====================================

def get_episode(text):

    match = re.search(
        r'Episode[s]?\s*([\d\-]+)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None

# ====================================
# DUPLICATE ID
# ====================================

def create_post_id(
    title,
    season,
    episode
):

    title = (
        title or ""
    ).lower().strip()

    season = (
        season or ""
    ).strip()

    episode = (
        episode or ""
    ).strip()

    return f"{title}|{season}|{episode}"

# ====================================
# CLEAN TITLE
# ====================================

def clean_title_from_url(text):

    url = get_url(text)

    if not url:
        return None

    try:

        slug = url.split("/")[-2]

        slug = slug.replace("-", " ")

        return slug.title().strip()

    except:
        return None

# ====================================
# TMDB SEARCH
# ====================================

def get_tmdb_id(
    title,
    movie=False
):

    if movie:
        url = "https://api.themoviedb.org/3/search/movie"
    else:
        url = "https://api.themoviedb.org/3/search/tv"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }

    try:

        response = requests.get(
            url,
            params=params
        )

        data = response.json()

        if data.get("results"):

            return data["results"][0]["id"]

    except:
        return None

    return None

# ====================================
# CREATE CAPTION
# ====================================

def create_caption(text):

    title = clean_title_from_url(text)

    if not title:
        return None

    season = get_season(text)
    episode = get_episode(text)

    tmdb_id = get_tmdb_id(title)

    if not tmdb_id:
        return None

    tgflix_link = (
        f"https://tgflix.lovable.app/series/{tmdb_id}"
    )

    caption = f'''
╭──────────────⭓
┃ 🎬 {title}
╰──────────────⭓

🔗 WATCH NOW:
{tgflix_link}

━━━━━━━━━━━━━━━
🔥 Powered By TGFLIX
━━━━━━━━━━━━━━━
'''

    return caption.strip()

# ====================================
# MAIN BOT
# ====================================

async def main():

    await send_log(
        "🟢 TGFLIX BOT STARTED"
    )

    @client.on(events.NewMessage())
    async def handler(event):

        msg = event.message

        text = msg.text or ""

        chat_id = event.chat_id

        print("\nNEW POST:")
        print(text)

        # ====================================
        # TELEGRAM ADMIN COMMANDS
        # ====================================

        if chat_id == ADMIN_CHANNEL_ID:

            if text.startswith("/help"):

                await event.reply(
                    '''
🤖 TGFLIX BOT COMMANDS

🏓 /ping
📊 /stats
📈 /status
⏰ /uptime

📡 /sources
🎯 /targets

➕ /addsource -100xxxx
➖ /removesource -100xxxx

➕ /addtarget -100xxxx
➖ /removetarget -100xxxx

📢 /broadcast message
📜 /logs
🧪 /test

⏸ /pause -100xxxx
▶️ /unpause -100xxxx

❓ /help
'''
                )

                return

        # ====================================
        # IGNORE NON SOURCES
        # ====================================

        if chat_id not in SOURCE_IDS:
            return

        # ====================================
        # CREATE CAPTION
        # ====================================

        new_caption = create_caption(text)

        if not new_caption:

            stats["skipped"] += 1

            return

        # ====================================
        # DUPLICATE CHECK
        # ====================================

        title = clean_title_from_url(text)

        season = get_season(text)

        episode = get_episode(text)

        post_id = create_post_id(
            title,
            season,
            episode
        )

        if post_id in sent_cache:

            stats["duplicates"] += 1

            duplicate_msg = (
                f"🧠 DUPLICATE → {post_id}"
            )

            await add_recent_log(
                duplicate_msg
            )

            await send_log(
                duplicate_msg
            )

            return

        sent_cache.add(post_id)

        # ====================================
        # SEND TO TARGETS
        # ====================================

        for target in TARGET_IDS:

            if target in paused_targets:
                continue

            try:

                if msg.photo:

                    await client.send_file(
                        target,
                        msg.photo,
                        caption=new_caption
                    )

                else:

                    await client.send_message(
                        target,
                        new_caption,
                        link_preview=False
                    )

                stats["sent"] += 1

                sent_msg = (
                    f"✅ SENT → {target}"
                )

                await add_recent_log(
                    sent_msg
                )

                await send_log(
                    sent_msg
                )

            except Exception as e:

                stats["errors"] += 1

                error_msg = (
                    f"❌ ERROR → {e}"
                )

                await add_recent_log(
                    error_msg
                )

                await send_log(
                    error_msg
                )

    print("BOT RUNNING...")

    await client.run_until_disconnected()

# ====================================
# START EVERYTHING
# ====================================

threading.Thread(
    target=run_web
).start()

with client:
    client.loop.run_until_complete(main())

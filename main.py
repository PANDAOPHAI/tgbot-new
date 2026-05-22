from telethon import TelegramClient, events
from flask import Flask
import threading
import requests
import re
import os
import time

# ====================================
# FLASK SERVER
# ====================================

app = Flask(__name__)

@app.route('/')
def home():
    return "TGFLIX BOT RUNNING"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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
# DUPLICATE CACHE
# ====================================

sent_cache = set()

# ====================================
# PAUSED TARGETS
# ====================================

paused_targets = set()

# ====================================
# RECENT LOGS
# ====================================

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

    seconds = int(time.time() - start_time)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours}h {minutes}m {secs}s"

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
# NEWS POST CHECK
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

    url = get_url(text)

    if url:

        match = re.search(
            r'season-(\d+)',
            url,
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

def create_post_id(title, season, episode):

    title = (title or "").lower().strip()
    season = (season or "").strip()
    episode = (episode or "").strip()

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

        remove_patterns = [
            r'-movie',
            r'-season-\d+',
            r'-episodes-hindi-subbed-download-hd',
            r'-episodes-hindi-dubbed-download-hd',
            r'-hindi-episodes-download-hd',
            r'-hindi-subbed-download-hd',
            r'-hindi-dubbed-download-hd',
            r'-episodes-download-hd',
            r'-episodes',
            r'-download',
            r'-hindi-subbed',
            r'-hindi-dubbed',
            r'-english-subbed',
            r'-english-dubbed',
            r'-tamil-dubbed',
            r'-telugu-dubbed',
            r'-multi-audio',
            r'-multi-sub',
            r'-subbed',
            r'-dubbed',
            r'-hd',
            r'-zip-pack',
            r'-\d{4}'
        ]

        for pattern in remove_patterns:
            slug = re.sub(pattern, '', slug)

        slug = slug.replace("-", " ")

        return slug.title().strip()

    except:
        return None

# ====================================
# CLEAN NEWS TITLE
# ====================================

def clean_title_from_news(text):

    lines = text.splitlines()

    merged = " ".join(lines[:2])

    remove_words = [
        "officially announced",
        "release date",
        "coming soon",
        "set to release",
        "this summer 2026",
        "( no specific date )",
        "hindi dub"
    ]

    cleaned = merged

    for word in remove_words:

        cleaned = re.sub(
            word,
            '',
            cleaned,
            flags=re.IGNORECASE
        )

    cleaned = re.sub(
        r'Season\s*\d+',
        '',
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r'\s+',
        ' ',
        cleaned
    )

    return cleaned.strip(" -!:")

# ====================================
# LANGUAGE DETECT
# ====================================

def get_language_type(text):

    text = text.lower()

    if "multi-audio" in text:
        audio = "Multi Audio"

    elif "dubbed" in text:
        audio = "Dubbed"

    elif "subbed" in text:
        audio = "Subbed"

    else:
        audio = "Subbed"

    if "hindi" in text:
        lang = "Hindi"

    elif "english" in text:
        lang = "English"

    elif "tamil" in text:
        lang = "Tamil"

    elif "telugu" in text:
        lang = "Telugu"

    else:
        lang = ""

    if lang:
        return f"{lang} {audio}"

    return audio

# ====================================
# TMDB SEARCH
# ====================================

def get_tmdb_id(title, movie=False):

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

    except Exception as e:
        print("TMDB ERROR:", e)

    return None

# ====================================
# DOWNLOAD POST
# ====================================

def create_download_caption(text):

    title = clean_title_from_url(text)

    if not title:
        return None

    movie = is_movie(text)

    season = get_season(text)

    episode = get_episode(text)

    language_type = get_language_type(text)

    tmdb_id = get_tmdb_id(title, movie)

    if not tmdb_id:
        return None

    if movie:
        tgflix_link = f"https://tgflix.lovable.app/movie/{tmdb_id}"
    else:
        tgflix_link = f"https://tgflix.lovable.app/series/{tmdb_id}"

    complete_season = False

    text_lower = text.lower()

    if "complete season" in text_lower:
        complete_season = True

    if "zip pack" in text_lower:
        complete_season = True

    play_link = None

    if not movie and season:

        play_episode = "1"

        if episode:

            first_ep = episode.split("-")[0]

            if first_ep.strip():
                play_episode = first_ep

        play_link = (
            f"https://tgflix.lovable.app/play-series/"
            f"{tmdb_id}/{season}/{play_episode}"
        )

    title_line = f"🎬 {title}"

    if season:
        title_line += f" • Season {season.zfill(2)}"

    if episode:
        title_line += f" • Episode {episode}"

    caption = f'''
╭──────────────⭓
┃ {title_line}
╰──────────────⭓
'''

    if complete_season:

        caption += f'''

📦 Complete Season Added
🌐 Audio: {language_type}

🔗 WATCH NOW:
{tgflix_link}
'''

    else:

        caption += f'''

✨ Status: Added
🌐 Audio: {language_type}

🔗 WATCH NOW:
{tgflix_link}
'''

    if play_link:

        caption += f'''

▶️ PLAY NOW:
{play_link}
'''

    caption += '''

━━━━━━━━━━━━━━━
🔥 Powered By TGFLIX
━━━━━━━━━━━━━━━
'''

    return caption.strip()

# ====================================
# NEWS POST
# ====================================

def create_news_caption(text):

    title = clean_title_from_news(text)

    if not title:
        return None

    season = get_season(text)

    tmdb_id = get_tmdb_id(title)

    if not tmdb_id:
        return None

    tgflix_link = (
        f"https://tgflix.lovable.app/series/{tmdb_id}"
    )

    lines = text.splitlines()

    cleaned_lines = []

    blocked_words = [
        "rareanimes",
        "stay tuned",
        "rai"
    ]

    for line in lines:

        line_lower = line.lower()

        skip = False

        for word in blocked_words:

            if word in line_lower:
                skip = True
                break

        if not skip and line.strip():
            cleaned_lines.append(line.strip())

    cleaned_text = "\n\n".join(cleaned_lines)

    title_line = f"🎬 {title}"

    if season:
        title_line += f" • Season {season.zfill(2)}"

    caption = f'''
╭──────────────⭓
┃ {title_line}
╰──────────────⭓

{cleaned_text}

🔗 WATCH S01 NOW:
{tgflix_link}

━━━━━━━━━━━━━━━
🔥 Powered By TGFLIX
━━━━━━━━━━━━━━━
'''

    return caption.strip()

# ====================================
# FINAL CAPTION
# ====================================

def create_caption(text):

    text_lower = text.lower()

    if is_news_post(text):
        return create_news_caption(text)

    download_keywords = [
        "rareanimes.buzz",
        "episode",
        "episodes",
        "movie",
        "complete season",
        "zip pack",
        "added"
    ]

    matched = False

    for word in download_keywords:

        if word in text_lower:
            matched = True
            break

    if matched:
        return create_download_caption(text)

    return None

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
        print("CHAT ID:", chat_id)

        # ====================================
        # ADMIN COMMANDS
        # ====================================

        if chat_id == ADMIN_CHANNEL_ID:

            # /help
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

📜 /logs
🧪 /test

⏸ /pause -100xxxx
▶️ /unpause -100xxxx
'''
                )

                return

            # /ping
            if text.startswith("/ping"):

                ping_ms = round(
                    client.loop.time() * 1000
                ) % 1000

                await event.reply(
                    f'''
🏓 PONG

⚡ Ping: {ping_ms}ms
'''
                )

                return

            # /stats
            if text.startswith("/stats"):

                await event.reply(
                    f'''
📊 TGFLIX STATS

✅ Sent: {stats['sent']}
⚠️ Skipped: {stats['skipped']}
❌ Errors: {stats['errors']}
🧠 Duplicates: {stats['duplicates']}
'''
                )

                return

            # /status
            if text.startswith("/status"):

                active_targets = (
                    len(TARGET_IDS)
                    - len(paused_targets)
                )

                paused_count = len(paused_targets)

                await event.reply(
                    f'''
🤖 TGFLIX STATUS

🟢 Bot: ONLINE

📡 Sources: {len(SOURCE_IDS)}
🎯 Targets: {len(TARGET_IDS)}

▶️ Active: {active_targets}
⏸ Paused: {paused_count}

🕒 Uptime:
{get_uptime()}
'''
                )

                return

            # /logs
            if text.startswith("/logs"):

                if not recent_logs:

                    await event.reply(
                        "❌ No Logs"
                    )

                else:

                    log_text = "\n\n".join(
                        recent_logs[-10:]
                    )

                    await event.reply(
                        f'''
📜 RECENT LOGS

{log_text}
'''
                    )

                return

            # /test
            if text.startswith("/test"):

                await event.reply(
                    "✅ TEST SUCCESS"
                )

                return

        # ====================================
        # IGNORE NON SOURCE CHANNELS
        # ====================================

        if chat_id not in SOURCE_IDS:
            return

        # ====================================
        # CREATE CAPTION
        # ====================================

        new_caption = create_caption(text)

        if not new_caption:

            stats["skipped"] += 1

            await add_recent_log(
                f"⚠️ SKIPPED → {text[:50]}"
            )

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

            print(duplicate_msg)

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

                elif msg.video:

                    await client.send_file(
                        target,
                        msg.video,
                        caption=new_caption
                    )

                elif msg.document:

                    await client.send_file(
                        target,
                        msg.document,
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

                print(sent_msg)

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

                print(error_msg)

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

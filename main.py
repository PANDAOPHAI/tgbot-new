from telethon import TelegramClient, events
from flask import Flask
import threading
import requests
import re
import os

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
# CHANNEL IDS
# ====================================

SOURCE_ID = -1003900368405

# MULTIPLE TARGET CHANNELS
TARGET_IDS = [
    -1003927415038,
    -1003913101784
]

# ====================================
# CLIENT
# ====================================

client = TelegramClient("session", api_id, api_hash)

# ====================================
# GET URL
# ====================================

def get_url(text):

    match = re.search(r'https?://\S+', text)

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

    # TEXT SEASON
    match = re.search(
        r'Season\s*(\d+)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    # URL SEASON
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
# CLEAN TITLE FROM URL
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
            r'-\d{4}'
        ]

        for pattern in remove_patterns:
            slug = re.sub(pattern, '', slug)

        slug = slug.replace("-", " ")

        return slug.title().strip()

    except:
        return None

# ====================================
# CLEAN TITLE FROM NEWS POST
# ====================================

def clean_title_from_news(text):

    # MERGE FIRST 2 LINES
    lines = text.splitlines()

    merged = " ".join(lines[:2])

    # REMOVE NEWS WORDS
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

    # REMOVE SEASON TEMP
    cleaned = re.sub(
        r'Season\s*\d+',
        '',
        cleaned,
        flags=re.IGNORECASE
    )

    # CLEAN SPACES
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip(" -!:")

# ====================================
# DETECT LANGUAGE
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

        response = requests.get(url, params=params)

        data = response.json()

        if data.get("results"):

            return data["results"][0]["id"]

    except:
        pass

    return None

# ====================================
# CREATE DOWNLOAD POST
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

    # ====================================
    # LINKS
    # ====================================

    # MAIN PAGE
    if movie:
        tgflix_link = f"https://tgflix.lovable.app/movie/{tmdb_id}"
    else:
        tgflix_link = f"https://tgflix.lovable.app/series/{tmdb_id}"

    # DIRECT PLAY LINK
    play_link = None

    if not movie and season and episode:

        first_ep = episode.split("-")[0]

        play_link = f"https://tgflix.lovable.app/play-series/{tmdb_id}/{season}/{first_ep}"

    # ====================================
    # TITLE
    # ====================================

    title_line = f"🎬 {title}"

    if season:
        title_line += f" • Season {season.zfill(2)}"

    if episode:
        title_line += f" • Episode {episode}"

    # ====================================
    # CAPTION
    # ====================================

    caption = f'''
╭──────────────⭓
┃ {title_line}
╰──────────────⭓

✨ Status: Added
🌐 Audio: {language_type}

🔗 WATCH NOW:
{tgflix_link}
'''

    # DIRECT PLAY LINK
    if play_link:

        caption += f'''

▶️ PLAY EPISODE:
{play_link}
'''

    caption += '''

━━━━━━━━━━━━━━━
🔥 Powered By TGFLIX
━━━━━━━━━━━━━━━
'''

    return caption.strip()

# ====================================
# CREATE NEWS POST
# ====================================

def create_news_caption(text):

    title = clean_title_from_news(text)

    if not title:
        return None

    season = get_season(text)

    tmdb_id = get_tmdb_id(title)

    if not tmdb_id:
        return None

    tgflix_link = f"https://tgflix.lovable.app/series/{tmdb_id}"

    # CLEAN UNWANTED LINES
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

    # TITLE LINE
    title_line = f"🎬 {title}"

    if season:
        title_line += f" • Season {season.zfill(2)}"

    # FINAL DESIGN
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
# CREATE FINAL CAPTION
# ====================================

def create_caption(text):

    # NEWS POSTS
    if is_news_post(text):
        return create_news_caption(text)

    # DOWNLOAD POSTS
    if "rareanimes.buzz" in text.lower():
        return create_download_caption(text)

    return None

# ====================================
# MAIN BOT
# ====================================

async def main():

    source_entity = await client.get_entity(SOURCE_ID)

    print("SOURCE LOADED:", source_entity.title)

    @client.on(events.NewMessage(chats=source_entity))
    async def handler(event):

        msg = event.message

        text = msg.text or ""

        print("\nNEW POST:")
        print(text)

        new_caption = create_caption(text)

        if not new_caption:
            print("SKIPPED")
            return

        try:

            # SEND TO ALL TARGET CHANNELS
            for target in TARGET_IDS:

                try:

                    # PHOTO
                    if msg.photo:

                        await client.send_file(
                            target,
                            msg.photo,
                            caption=new_caption
                        )

                    # VIDEO
                    elif msg.video:

                        await client.send_file(
                            target,
                            msg.video,
                            caption=new_caption
                        )

                    # DOCUMENT
                    elif msg.document:

                        await client.send_file(
                            target,
                            msg.document,
                            caption=new_caption
                        )

                    # TEXT
                    else:

                        await client.send_message(
                            target,
                            new_caption,
                            link_preview=False
                        )

                    print(f"POST SENT TO {target}")

                except Exception as e:

                    print(f"FAILED {target}: {e}")

        except Exception as e:

            print("SEND ERROR:", e)

    print("BOT RUNNING...")

    await client.run_until_disconnected()

# ====================================
# START EVERYTHING
# ====================================

threading.Thread(target=run_web).start()

with client:
    client.loop.run_until_complete(main())

from telethon import TelegramClient, events
from flask import Flask
import threading
import requests
import re
import os

# ====================================
# FLASK SERVER (FOR RENDER)
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

api_id = 123456
api_hash = "YOUR_API_HASH"

# ====================================
# TMDB API
# ====================================

TMDB_API_KEY = "f1e46d83ecce5dc29c90d9d2ed41f2ed"

# ====================================
# CHANNEL IDS
# ====================================

SOURCE_ID = -1003900368405
TARGET_ID = -1003927415038

# ====================================
# CREATE CLIENT
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
# MOVIE CHECK
# ====================================

def is_movie(text):

    text = text.lower()

    return "movie" in text

# ====================================
# CLEAN TITLE
# ====================================

def clean_title(text):

    url = get_url(text)

    if url:

        try:

            slug = url.split("/")[-2]

            remove_parts = [
                "-movie",
                "-season-1",
                "-season-2",
                "-season-3",
                "-season-4",
                "-season-5",
                "-hindi-dubbed-episodes-download-hd",
                "-episodes-download-hd",
                "-episodes",
                "-download",
                "-hindi-dubbed",
                "-english-dubbed",
                "-tamil-dubbed",
                "-telugu-dubbed",
                "-multi-audio",
                "-multi-sub",
                "-subbed",
                "-dubbed",
                "-hd"
            ]

            for part in remove_parts:
                slug = slug.replace(part, "")

            slug = re.sub(r'-\d{4}', '', slug)

            slug = re.sub(r'-season-\d+', '', slug)

            slug = slug.replace("-", " ")

            return slug.title().strip()

        except:
            pass

    return None

# ====================================
# GET EPISODE
# ====================================

def get_episode(text):

    match = re.search(
        r'Episode\s*(\d+)',
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None

# ====================================
# GET SEASON
# ====================================

def get_season(text):

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
# DETECT LANGUAGE
# ====================================

def get_language_type(text):

    text = text.lower()

    # AUDIO
    if "multi-audio" in text:
        audio = "Multi Audio"

    elif "dubbed" in text:
        audio = "Dubbed"

    elif "subbed" in text:
        audio = "Subbed"

    else:
        audio = "Subbed"

    # LANGUAGE
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
# GET TMDB ID
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

            first = data["results"][0]

            print("TMDB FOUND:", first.get("title") or first.get("name"))

            return first["id"]

    except Exception as e:
        print("TMDB ERROR:", e)

    return None

# ====================================
# CREATE CAPTION
# ====================================

def create_caption(text):

    title = clean_title(text)

    if not title:
        return None

    movie = is_movie(text)

    episode = get_episode(text)

    season = get_season(text)

    language_type = get_language_type(text)

    tmdb_id = get_tmdb_id(title, movie)

    if not tmdb_id:
        return None

    # LINK
    if movie:
        tgflix_link = f"https://tgflix.lovable.app/movie/{tmdb_id}"
    else:
        tgflix_link = f"https://tgflix.lovable.app/series/{tmdb_id}"

    # TITLE
    title_line = f"🎬 {title}"

    if season:
        title_line += f" • Season {season}"

    if episode:
        title_line += f" • Episode {episode}"

    # FINAL DESIGN
    caption = f"""
╭──────────────⭓
┃ {title_line}
╰──────────────⭓

✨ Status: Added
🌐 Audio: {language_type}

🔗 WATCH NOW:
{tgflix_link}

━━━━━━━━━━━━━━━
🔥 Powered By TGFLIX
━━━━━━━━━━━━━━━
"""

    return caption.strip()

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
            return

        try:

            if msg.photo:

                await client.send_file(
                    TARGET_ID,
                    msg.photo,
                    caption=new_caption
                )

            elif msg.video:

                await client.send_file(
                    TARGET_ID,
                    msg.video,
                    caption=new_caption
                )

            elif msg.document:

                await client.send_file(
                    TARGET_ID,
                    msg.document,
                    caption=new_caption
                )

            else:

                await client.send_message(
                    TARGET_ID,
                    new_caption,
                    link_preview=False
                )

            print("POST COPIED")

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
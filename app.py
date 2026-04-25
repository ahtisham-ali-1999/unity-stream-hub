from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import re

app = Flask(__name__)

# -------------------------
# DOWNLOAD FOLDER
# -------------------------
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -------------------------
# COOKIE PATH
# -------------------------
COOKIE_PATH = os.path.join(os.path.dirname(__file__), "cookie.txt")

# -------------------------
# FILE NAME SANITIZER
# -------------------------
def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|：｜]', "", name)


# -------------------------
# LANDING PAGE
# -------------------------
@app.route("/")
def landing():
    return render_template("landing.html")


# -------------------------
# MAIN APP
# -------------------------
@app.route("/app", methods=["GET", "POST"])
def index():

    formats = []
    url = ""
    title = ""
    thumbnail = ""

    if request.method == "POST":

        url = request.form.get("url")

        # -------------------------
        # FETCH VIDEO INFO
        # -------------------------
        if "get_formats" in request.form:

            allowed = [240, 360, 720, 1080]
            seen = set()

            ydl_opts = {
                "cookiefile": COOKIE_PATH,
                "quiet": True,
                "noplaylist": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title = info.get("title")
            thumbnail = info.get("thumbnail")

            for f in info.get("formats", []):
                h = f.get("height")

                if h in allowed and h not in seen:
                    formats.append({
                        "format_id": f["format_id"],
                        "label": f"{h}p"
                    })
                    seen.add(h)

            return render_template(
                "index.html",
                formats=formats,
                url=url,
                title=title,
                thumbnail=thumbnail
            )

        # -------------------------
        # VIDEO DOWNLOAD
        # -------------------------
        if "download" in request.form:

            format_id = request.form.get("format")

            ydl_opts = {
                "cookiefile": COOKIE_PATH,
                "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
                "format": f"{format_id}+bestaudio/best",
                "noplaylist": True,
                "quiet": True,
                "merge_output_format": "mp4"
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                filepath = os.path.splitext(filepath)[0] + ".mp4"

            if not os.path.exists(filepath):
                return "Download failed: file not found"

            response = send_file(filepath, as_attachment=True)
            response.set_cookie('download_ready', '1')
            return response

        # -------------------------
        # MP3 DOWNLOAD
        # -------------------------
        if "mp3" in request.form:

            ydl_opts = {
                "cookiefile": COOKIE_PATH,
                "format": "bestaudio/best",
                "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                filepath = os.path.splitext(filepath)[0] + ".mp3"

            if not os.path.exists(filepath):
                return "MP3 conversion failed"

            response = send_file(filepath, as_attachment=True)
            response.set_cookie('download_ready', '1')
            return response

    return render_template(
        "index.html",
        formats=[],
        url="",
        title="",
        thumbnail=""
    )


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
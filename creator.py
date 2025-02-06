import spotipy
import requests
import time
from spotipy.client import SpotifyException
from datetime import datetime, timezone
from io import BytesIO
from PIL import Image
import base64
import threading
from flask import Flask
import os

# Spotify API credentials
CLIENT_ID = "e23837e75d6b4e5d99d4e19dd9e23480"
CLIENT_SECRET = "c5e1283ae5114db5bbf68980b56c5805"
REFRESH_TOKEN = "AQD-ud0O60rwsRKqOjqjsi-akdU0oIx1yy7xFUGENKQdb8ZMyRtLgqXcawgW7iBVloPBu8JpqB9ZgSZ-hJJoEz5L_EZDbULh7grJsE7BImnkgD0OCJe4cUxa1fSHP2H8ozg"  # Replace with your actual refresh token
TOKEN_URL = "https://accounts.spotify.com/api/token"

def refresh_access_token():
    """Refresh the Spotify access token."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=payload)
    token_info = response.json()
    
    if "access_token" not in token_info:
        print("❌ ERROR: Failed to refresh access token:", token_info)
        raise Exception("Failed to refresh access token. Check credentials and refresh token.")
    
    print("✅ Successfully refreshed access token.")
    return token_info["access_token"]

# Initialize Spotify client with refreshed token
ACCESS_TOKEN = refresh_access_token()
sp = spotipy.Spotify(auth=ACCESS_TOKEN)

def get_spotify_client():
    """Refresh token and return a new Spotify client."""
    global ACCESS_TOKEN, sp
    ACCESS_TOKEN = refresh_access_token()
    sp = spotipy.Spotify(auth=ACCESS_TOKEN)
    return sp

# Playlist tracking variables
count = 0
total = 0
track_uris = []
cover_img = []
previous_time = []
current_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
previous_time.append(current_time)

print("🎵 Starting Spotify tracking...")

def spotify_tracking_loop():
    """Continuously tracks played songs and creates playlists."""
    global count, total, track_uris, cover_img, previous_time, current_time
    
    while True:
        try:
            print("🔄 Checking Spotify API for recently played tracks...")
            sp = get_spotify_client()  # Always use a fresh access token

            if datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).date() != datetime.fromisoformat(current_time.replace("Z", "+00:00")).date():
                print("🎶 Creating new daily playlist...")

                total = str(int(total / count)) if count > 0 else "0"
                playlist_name = f"mixtape/{datetime.now().date()}"
                user_id = sp.current_user()["id"]
                print(f"👤 User ID: {user_id}")
                
                new_playlist = sp.user_playlist_create(
                    user=user_id,
                    name=playlist_name,
                    description=f"i'm feeling a light to decent {total}"
                )

                print(f"✅ Created playlist: {playlist_name}")

                if track_uris:
                    sp.playlist_add_items(playlist_id=new_playlist["id"], items=track_uris)
                    print(f"📀 Added {len(track_uris)} tracks to playlist.")

                # Blend images
                if cover_img:
                    print("🖼️ Blending cover images...")
                    blended_img = cover_img[0]
                    for img in cover_img[1:]:
                        blended_img = Image.blend(blended_img, img, 0.2)
                    blended_img.save("encode.jpg")

                    # Upload cover image
                    with open("encode.jpg", "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    sp.playlist_upload_cover_image(playlist_id=new_playlist["id"], image_b64=encoded_string)
                    print("✅ Uploaded custom playlist cover.")

                # Reset for new day
                track_uris = []
                cover_img = []
                count = 0
                total = 0

            else:
                current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                previous_time.append(current_time)

                results = sp.current_user_recently_played(limit=50)

                for idx, item in enumerate(results["items"]):
                    if previous_time[-2] < item["played_at"] < current_time:
                        track = item["track"]
                        if track["uri"] not in track_uris:
                            total += track["popularity"]
                            count += 1
                            img_url = track["album"]["images"][0]["url"]
                            response = requests.get(img_url)
                            cover_img.append(Image.open(BytesIO(response.content)))

                        track_uris.append(track["uri"])

                print(f"✅ Checked at {datetime.now()}: {len(track_uris)} total tracks found.")

            time.sleep(300)  # Check every 5 minutes

        except SpotifyException as e:
            print("❌ Spotify API error:", e)
            time.sleep(10)  # Wait before retrying

        except Exception as e:
            print("❌ Unexpected error:", e)
            time.sleep(30)  # Avoid crashing the script

# Start the Spotify tracking loop in a separate thread
tracking_thread = threading.Thread(target=spotify_tracking_loop)
tracking_thread.daemon = True  # Keeps running in the background
tracking_thread.start()

# Flask app for Render (to keep service alive)
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Spotify bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets the port dynamically
    app.run(host="0.0.0.0", port=port)

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, time, date, timedelta
import requests
from io import BytesIO
from PIL import Image
import base64

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

print("1")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=["user-read-recently-played" ,"playlist-modify-public", "user-read-private", "ugc-image-upload"],
    cache_path=".cache"
))

current_time = datetime.combine(datetime.now(), time.min)
with open('time.txt', 'r') as file:
    createtime = file.read().rstrip()
print(current_time)

token_info = sp.auth_manager.get_cached_token()
if not token_info:
    print("❌ ERROR: No access token retrieved!")
    exit(1)
else:
    print("✅ Token retrieved successfully.")
results = sp.current_user_recently_played(limit=50)
print("3")
track_uris = []
cover_img = []
playlist_name = "mixtape/"+ str(date(day=datetime.now().day ,month=datetime.now().month ,year=datetime.now().year))
playlists = sp.current_user_playlists()
exists = True
for idx, item in enumerate(playlists['items']):
    print(item['name'])
    if item['name'] == playlist_name:
        mixtape_id = item['id']
        with open('time.txt', 'r') as file:
            current_time = file.read().rstrip()
            current_time = datetime.strptime(current_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            exists = False
        break
if exists:
    img = Image.open("w.jpg")
else:
    temp = sp.playlist_cover_image(mixtape_id)
    response = requests.get(temp[0]['url'])
    img = Image.open(BytesIO(response.content))
img.save("temp.jpg")
for idx, item in enumerate(results['items']):
    played_at_str = item['played_at']
    try:
        played_at_time = datetime.strptime(played_at_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        played_at_time = datetime.strptime(played_at_str, "%Y-%m-%dT%H:%M:%SZ")
    if played_at_time > current_time:
        if idx == 0:
            createtime = item['played_at']
        track = item['track']
        if track['uri'] not in track_uris:
            temp = track['album']['images'][0]['url']
            response = requests.get(temp)
            tempimg = Image.open(BytesIO(response.content))
            cover_img.append(tempimg)
        track_uris.append(track['uri'])
        print(idx, track['artists'][0]['name'], " – ", track['name'],)
with open('time.txt', 'w') as file:
    file.seek(0)
    file.truncate()
    file.write(str(createtime))
if exists:
    new_playlist = sp.user_playlist_create(user=sp.current_user()['id'],name=playlist_name)
    mixtape_id = new_playlist['id']
    if track_uris:
        sp.playlist_add_items(playlist_id=mixtape_id, items=track_uris)
else:
    if track_uris:
        sp.playlist_add_items(playlist_id=mixtape_id, items=track_uris, position=0)
results = sp.playlist_tracks(playlist_id=mixtape_id)
total = 0
count = 0
track_uris = []
for idx, item in enumerate(results['items']):
    track = item['track']
    if track['uri'] not in track_uris:
        total = total + track['popularity']
        count += 1
if count!=0:
    total = int(total/count)
if datetime.now().hour > 23:
    new_playlist = sp.playlist_change_details(playlist_id=mixtape_id,name=playlist_name,public=False,description="i'm feeling a light to decent " + str(total))
else:
    new_playlist = sp.playlist_change_details(playlist_id=mixtape_id,name=playlist_name,description="i'm feeling a light to decent " + str(total))
for image in cover_img:
    image = image.resize(img.size)
    image = image.convert("RGB")
    img = img.convert("RGB")
    img = Image.blend(img, image, 0.2)
img.save("encode.jpg")
image_path = "encode.jpg"
with open(image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
sp.playlist_upload_cover_image(playlist_id=mixtape_id, image_b64=encoded_string)

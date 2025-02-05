import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, time, date, timedelta
import requests
from io import BytesIO
from PIL import Image
import requests
from io import BytesIO
import base64

img = Image.open("w.jpg").convert('L')
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="e23837e75d6b4e5d99d4e19dd9e23480",
                                               client_secret="c5e1283ae5114db5bbf68980b56c5805",
                                               redirect_uri="http://localhost:8888/callback",
                                               scope=["user-read-recently-played","playlist-modify-public","user-read-private","ugc-image-upload"]))

current_time = datetime.combine(datetime.now(), time.min)
# yesterday_time = datetime.combine(date.today()-timedelta(1), time.min)
results = sp.current_user_recently_played(limit=50)
count = 0
total = 0
track_uris = []
cover_img = []
for idx, item in enumerate(results['items']):
    # if item['played_at'] > str(yesterday_time) and item['played_at'] < str(current_time):
    if item['played_at'] > str(current_time):
        track = item['track']
        print(track)
        if track['uri'] not in track_uris:
            total = total + track['popularity']
            count += 1
            temp = track['album']['images'][0]['url']
            response = requests.get(temp)
            img = Image.open(BytesIO(response.content))
            cover_img.append(img)
            # track_uris.append(track['uri'])
        track_uris.append(track['uri'])
        print(idx, track['artists'][0]['name'], " – ", track['name'],)
total = str(int(total/count))
playlist_name = "mixtape/"+ str(date(day=current_time.day ,month=current_time.month ,year=current_time.year))
new_playlist = sp.user_playlist_create(user=sp.current_user()['id'],name=playlist_name, description="i'm feeling a light to decent " + total)
if track_uris:
    sp.playlist_add_items(playlist_id=new_playlist['id'], items=track_uris)
for image in cover_img:
    img = Image.blend(img, image, 0.2)
img.save("encode.jpg")
image_path = "encode.jpg"
with open(image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
sp.playlist_upload_cover_image(playlist_id=new_playlist['id'], image_b64=encoded_string)








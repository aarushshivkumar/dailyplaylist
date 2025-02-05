import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, date, timezone
import time
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
                                               scope=["user-read-recently-played","playlist-modify-public","user-read-private","ugc-image-upload","user-read-currently-playing"]))

count = 0
total = 0
track_uris = []
cover_img = []
previous_time = []
current_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
previous_time.append(current_time)
time.sleep(10)
print('starting')
while True:
    if datetime.now().hour>=23 and datetime.now().minute>59:
        break
    else:
        current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        previous_time.append(current_time)
        print("previous time : ", previous_time[-2])
        print("current time : ", current_time)
        results = sp.current_user_recently_played(limit=50)
        for idx, item in enumerate(results['items']):
            track = item['track']
            print(item['played_at'])
            if item['played_at'] > str(previous_time[-2]) and item['played_at'] < str(current_time):
                track = item['track']
                print("matched : ", track)
                if track['uri'] not in track_uris:
                    total = total + track['popularity']
                    count += 1
                    temp = track['album']['images'][0]['url']
                    response = requests.get(temp)
                    img = Image.open(BytesIO(response.content))
                    cover_img.append(img)
                track_uris.append(track['uri'])
                print(idx, track['artists'][0]['name'], " – ", track['name'],)
        time.sleep(300)
        print(datetime.now())
    

total = str(int(total/count))
playlist_name = "mixtape/"+ str(date(day=datetime.now().day ,month=datetime.now().month ,year=datetime.now().year))
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

#!/usr/bin/env python
# coding: utf-8

# https://www.linkedin.com/pulse/extracting-your-fav-playlist-info-spotifys-api-samantha-jones/

# # GET SONGS IN PLAYLIST
from __future__ import unicode_literals
import os
from random import random
from random import seed

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import youtube_dl


from youtubesearchpython import VideosSearch

from flask import Flask, render_template, request, flash, send_file

# %pip install pandas


cid = 'f231710a9c3d4d8f8ca9062d5231a7e2'
secret = '2650a1f988dd4f5bae7972c3c22a8a1c'

client_credentials_manager = SpotifyClientCredentials(
    client_id=cid, client_secret=secret)

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def call_playlist(creator, playlist_id):

    # step1

    playlist_features_list = ["artist", "album", "track_name",  "track_id", "danceability", "energy", "key", "loudness",
                              "mode", "speechiness", "instrumentalness", "liveness", "valence", "tempo", "duration_ms", "time_signature"]

    playlist_df = pd.DataFrame(columns=playlist_features_list)

    # step2

    playlist = sp.user_playlist_tracks(creator, playlist_id)["items"]
    for track in playlist:
        # Create empty dict
        playlist_features = {}
        # Get metadata
        playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
        playlist_features["album"] = track["track"]["album"]["name"]
        playlist_features["track_name"] = track["track"]["name"]
        playlist_features["track_id"] = track["track"]["id"]

        # Get audio features
        audio_features = sp.audio_features(playlist_features["track_id"])[0]
        for feature in playlist_features_list[4:]:
            playlist_features[feature] = audio_features[feature]

        # Concat the dfs
        track_df = pd.DataFrame(playlist_features, index=[0])
        playlist_df = pd.concat([playlist_df, track_df], ignore_index=True)

    # Step 3

    return playlist_df


# we only need the playlist id part of the link so we have to isolate it
def GenQueries(link):
    # "https://open.spotify.com/playlist/3Jh86SOjLQuEsLBCqHhwUv?si=f8421365d6454777"
    q_mark = link.find('?')
    playlist_id = link[34:q_mark]
    playlist = call_playlist("spotify", playlist_id)
    # https://open.spotify.com/playlist/5tFpMQzPaO9ZrMr7K1SgWr?si=f91194ec8ee4493a
    df = playlist
    queries = []

    for i in range(len(df)):
        #     print(df.iloc[i][1] + " by " + df.iloc[i][0])
        #     print(df.iloc[i][2], df.iloc[i][0],"audio")
        q = f"{df.iloc[i][2]} {df.iloc[i][0]} lyrics"
        queries.append(q)

    links = []
    names = []

    for query in queries:
        # limit 2 but we only using 1 for now
        videosSearch = VideosSearch(query, limit=1)
        res = videosSearch.result()
        names.append(res['result'][0]['title'])
        links.append(res['result'][0]['link'])
    return links, names


# print(res)

# links # looks mint

# # DOWNLOAD THE LINKS

# %pip install youtube_dl

def DownloadMusic(video_url):
    os.mkdir("./spotify-2-mp3")
    video_info = youtube_dl.YoutubeDL().extract_info(
        url=video_url, download=False
    )
    filename = f"{video_info['title']}.mp3"
    options = {
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': filename,
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl_opts = {
            'outtmpl': './spotify-2-mp3/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],

        }
        ydl.download([video_info['webpage_url']])

    print("Download complete... {}".format(filename))
    return filename

# url = 'https://www.youtube.com/watch?v=4XI-qWQpjas'


app = Flask(__name__)
seed(3)
app.config['SECRET_KEY'] = f'{random()}'


@app.route('/')
def home():
    try:
        os.rmdir("./spotify-2-mp3")
    except Exception as e:
        pass
    # flash('Songs are downloading, Be Patient')
    return render_template('home.html')


@app.route('/', methods=['GET', 'POST'])
def genmp3():
    links, names = GenQueries(request.form['url'])
    for url in links:
        file = DownloadMusic(url)
        print(url)
    if request.method == "POST":
        result = send_file("./spotify-2-mp3", as_attachment=True)
        return result
    else:
        return render_template('genmp3.html', titles=names),


@app.errorhandler(Exception)
def http_error_handler(error):
    flash("Something Bad Happened. Try Again or use a different link")
    return render_template("home.html")


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)

# links = GenQueries("https://open.spotify.com/playlist/57yftjkx1wMC6h1BGsmHs5?si=b3f81fd3bd3e44ca")

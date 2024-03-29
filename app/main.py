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
# from youtube_dl import YoutubeDL
from yt_dlp import YoutubeDL

import shutil

from youtubesearchpython import VideosSearch

import os, io
import webbrowser
from urllib.request import urlopen

from flask import Flask, render_template, request, flash, send_file, redirect, url_for

from waitress import serve, logging

from dotenv import load_dotenv
load_dotenv()

# pip install flask pandas youtube-search-python youtube_dl spotipy
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

cid = 'f231710a9c3d4d8f8ca9062d5231a7e2'
secret = os.environ.get('SECRET_KEY')

client_credentials_manager = SpotifyClientCredentials(
    client_id=cid, client_secret=secret)

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def call_playlist(creator, playlist_id):
    # print("PLAYLIST OCVER IMAGE:",sp.playlist_cover_image(playlist_id))
    
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

        # concat the dfs
        track_df = pd.DataFrame(playlist_features, index=[0])
        playlist_df = pd.concat([playlist_df, track_df], ignore_index=True)

    # step 3

    return playlist_df


# we only need the playlist id part of the link so we have to isolate it
def GenQueries(link):
    # "https://open.spotify.com/playlist/3Jh86SOjLQuEsLBCqHhwUv?si=f8421365d6454777"
    q_mark = link.find('?')
    playlist_id = link[34:q_mark]
    playlist = call_playlist("spotify", playlist_id)
    playlist_cover_image_src = sp.playlist_cover_image(playlist_id)

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
        try:
            videosSearch = VideosSearch(query, limit=1)
            res = videosSearch.result()
            names.append(res['result'][0]['title'])
            links.append(res['result'][0]['link'])
        except:
            pass
    return links, names, playlist_cover_image_src


# print(res)

# links # looks mint

# # DOWNLOAD THE LINKS


def DownloadMusic(video_url):
    
    video_info = YoutubeDL().extract_info(
        url=video_url, download=False
    )
    filename = f"{video_info['title']}.mp3"
    options = {
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': "spotify-2-mp3/"+filename,
        'quiet': True
    }

    with YoutubeDL(options) as ydl:
        ydl_opts = {
            'outtmpl': 'spotify-2-mp3/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,

        }
        ydl.download([video_info['webpage_url']])

    # print("Download complete... {}".format(filename))
    return filename
   
def ClearFolders():
    if os.path.isfile("spotify-2-mp3.zip"):
        os.remove("spotify-2-mp3.zip")

    if os.path.isdir("spotify-2-mp3"):
        shutil.rmtree("spotify-2-mp3")
        os.mkdir("spotify-2-mp3")

def ReadMultipleDataFrom(thisTextFile, thisPattern, file):
    inputData = []

    for iLine in file:
        if iLine.startswith(thisPattern):
            iLine = iLine.rstrip()
        if ('v=') in iLine:
            iLink = iLine.split('v=')[1]
            inputData.append(iLink) 
        if ('be/') in iLine:
            iLink =  iLine.split('be/')[1]
            inputData.append(iLink)
    return inputData

def gen_yt_playlist(links):
    inputFileName = links

    videoLinks =  ReadMultipleDataFrom(inputFileName, "https", links)

    short_links = [videoLinks[i:i + 50] for i in range(0, len(videoLinks), 50)]
    for l in short_links:
        listOfVideos = "http://www.youtube.com/watch_videos?video_ids=" + ','.join(l)
        response = urlopen(listOfVideos)
        playListLink = response.geturl()
        playListLink = playListLink.split('list=')[1]
        playListURL = "https://www.youtube.com/playlist?list="+playListLink+"&disable_polymer=true"
        # webbrowser.open(playListURL) # display the youtube playlist
        print(playListURL)
    return playListURL #kinda useless atm
    

app = Flask(__name__)
seed(3)
app.config['SECRET_KEY'] = f'{random()}'
app.config["CACHE_TYPE"] = "null"

@app.route('/')
def home():
    try:
        os.rmdir("spotify-2-mp3")
    except Exception as e:
        pass
    return render_template('home.html',)

@app.route('/download')
def download():
    #For windows you need to use drive name [ex: F:/Example.pdf]
    path = "../spotify-2-mp3.zip"
    print("downloading in /download")
    return send_file(path, as_attachment=True)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    playlist_cover_image_src = ""
    try:
        links, names, playlist_cover_image = GenQueries(request.form['url'])
        playlist_cover_image_src = playlist_cover_image[0]['url']
        print(playlist_cover_image_src)

    except Exception as e:
        flash('Invalid URL')
        print("Incorrect Playlist url used")
        return redirect(url_for('home'))
    
    # return redirect(url_for('home'))
    ClearFolders()
    print("Starting")
    short_pure_links = [links[i:i + 100] for i in range(0, len(links), 100)]

    for s in short_pure_links:
        playlist_url = gen_yt_playlist(s)
    
    for url in links:
        try:    
            DownloadMusic(url)
        except Exception as e:
            pass
        # send_file(file, as_attachment=True)
        # print(url)
    print("ALL DOWNLOADS COMPLETE")
    if request.method == "POST":
        #result =  send_file("spotify-2-mp3", as_attachment=True) # need to return send file
        # make_archive('spotify-2-mp3/', 'spotify-2-mp3.zip')
        shutil.make_archive("spotify-2-mp3", 'zip', "spotify-2-mp3")
        print("Created zip...")
        # res = send_file("../spotify-2-mp3.zip", as_attachment=True)
        # res = send_file("C:/Users/elect\Github/spotify-2-mp3/spotify-2-mp3.zip", as_attachment=True)
        # os.remove("C:/Users/elect\Github/spotify-2-mp3/spotify-2-mp3.zip")
        # os.remove("C:/Users/elect\Github/spotify-2-mp3/spotify-2-mp3")
        # return res
        # return render_template('download.html')
        # return send_file("spotify-2-mp3", as_attachment=True)
        return render_template('download.html', titles=names, playlist_url=playlist_url, playlist_cover_image_src=playlist_cover_image_src)
    else:
        print(playlist_cover_image_src)
        return render_template('generate.html', titles=names, playlist_url=playlist_url, playlist_cover_image_src=playlist_cover_image_src)


@app.errorhandler(Exception)
def http_error_handler(error):
    flash("Something Bad Happened. Try Again or use a different link")
    return render_template("home.html")


def Launch(): # for local only
    ClearFolders()
    app.run(host='0.0.0.0', port=5000, debug=False)
    app.run(debug=True, port=os.getenv("PORT", default=5000))


# links = GenQueries("https://open.spotify.com/playlist/3fp1SB3BHSGTn7UehTftQI?si=769d7743d40145dd")

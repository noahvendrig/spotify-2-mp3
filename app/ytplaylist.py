import os, io
import webbrowser
from urllib.request import urlopen

inputFileName = 'app/list.txt'

def ReadMultipleDataFrom(thisTextFile, thisPattern):
    inputData = []
    file = open(thisTextFile, "r")
    for iLine in file:
        if iLine.startswith(thisPattern):
            iLine = iLine.rstrip()
            # print iLine
        if ('v=') in iLine: # https://www.youtube.com/watch?v=aBcDeFGH
            iLink = iLine.split('v=')[1]
            inputData.append(iLink) 
        if ('be/') in iLine: # https://youtu.be/aBcDeFGH
            iLink =  iLine.split('be/')[1]
            inputData.append(iLink)
    return inputData

videoLinks =  ReadMultipleDataFrom(inputFileName, "https")  


n=50
new = [videoLinks[i:i + n] for i in range(0, len(videoLinks), n)]
print(len(new[-1]))

for n in new:
    listOfVideos = "http://www.youtube.com/watch_videos?video_ids=" + ','.join(videoLinks)
    # print listOfVideos

    response = urlopen(listOfVideos)
    playListLink = response.geturl()
    # print playListLink

    playListLink = playListLink.split('list=')[1]
    # print playListLink

    playListURL = "https://www.youtube.com/playlist?list="+playListLink+"&disable_polymer=true"

    print(playListURL)
    webbrowser.open(playListURL)
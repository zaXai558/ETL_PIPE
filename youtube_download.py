from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import pandas as pd

def configure():
    load_dotenv()

key = os.getenv("api_key")
cid = os.getenv("channel_id")
play_id = os.getenv("playlist_id")

youtube = build('youtube', 'v3', developerKey=key)

##Function to get channel stats
def get_channel_stats(youtube,cid):
    request= youtube.channels().list(
        part = 'snippet, contentDetails, statistics',
        forUsername=cid)
    response = request.execute()

    data= dict(Channel_name = response['items'][0]['snippet']['title'],
               Subscribers = response['items'][0]['statistics']['subscriberCount'],
               Views = response['items'][0]['statistics']['viewCount'],
               Total_vids = response['items'][0]['statistics']['videoCount'],
               upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
    return data

get_channel_stats(youtube,cid)


def get_video_ids(youtube, play_id):

    request = youtube.playlistItems().list(
        part = 'contentDetails',
        playlistId = play_id,
        maxResults =50)
    response = request.execute()

    video_ids = []

    for _ in range(len(response['items'])):
        video_ids.append(response['items'][_]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages =True

    while more_pages:
        if next_page_token is None:
            more_pages =False
        else:
            request = youtube.playlistItems().list(
                part = 'contentDetails',
                playlistId = play_id,
                maxResults =50,
                pageToken = next_page_token)
            response = request.execute()

            for _ in range(len(response['items'])):
                video_ids.append(response['items'][_]['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
    
    return video_ids

video_ids = get_video_ids(youtube, play_id)


#Details from videos
def get_video_details(youtube, video_ids):

    video_stats = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
        part='snippet,statistics',
        id=','.join(video_ids[i:i + 50])
        )
    response = request.execute()

    for video in response['items']:
        stats = dict(Title=video['snippet']['title'],
                     Publish_date=video['snippet']['publishedAt'],
                     Descriptions=video['snippet']['description'],
                     Tags=video['snippet'].get('tags', []),
                     Views=video['statistics']['viewCount'],
                     Likes=video['statistics']['likeCount'],
                     No_ofComments=video['statistics']['commentCount'],
                     )
        video_stats.append(stats)

    return video_stats


video_details = get_video_details(youtube, video_ids)

df = pd.DataFrame(video_details)

df.shape[0]









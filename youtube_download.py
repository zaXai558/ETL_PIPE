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

#Get Video ids
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

# As we can only send in 50 request a time so split the size to chunks
def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

extracted_data = []

# Iterate over chunks of IDs
for id_chunk in chunk_list(video_ids, 50):
    id_str = ','.join(id_chunk)
    request = youtube.videos().list(
        part="snippet,statistics",
        id=id_str
    )
    response = request.execute()

    # Process the response
    for item in response['items']:
        video_data = {
            'Title': item['snippet']['title'],
            'Publish_date': item['snippet']['publishedAt'],
            'Descriptions': item['snippet']['description'],
            'Tags': item['snippet'].get('tags', []),
            'Views': item['statistics']['viewCount'],
            'Likes': item['statistics']['likeCount'],
            'No_ofComments': item['statistics']['commentCount']}
        extracted_data.append(video_data)

for video_info in extracted_data:
    print(video_info)

df = pd.DataFrame(extracted_data)

df.shape[0]









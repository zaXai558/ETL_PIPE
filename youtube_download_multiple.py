from googleapiclient.discovery import build
import os
import pandas as pd

#Load API credentials from environment variables.
def load_credentials():

    api_key = os.getenv("api_key")
    
    if not api_key:
        raise ValueError("Please provide a valid API key.")

    return api_key

#Load channel IDs and playlist IDs from environment variables.Not working??
'''def load_channel_and_playlist_ids():

    channel_ids = os.getenv("channel_ids")
    playlist_ids = os.getenv("playlist_ids")
    
    if not channel_ids or not playlist_ids:
        raise ValueError("Please provide valid channel IDs and playlist IDs.")
    
    channel_ids = channel_ids.split(',')
    playlist_ids = playlist_ids.split(',')
    
    if len(channel_ids) != len(playlist_ids):
        raise ValueError("Number of channel IDs must match number of playlist IDs.")
    
    return channel_ids, playlist_ids'''

#YouTube API client.
def build_youtube_client(api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    return youtube

def get_channel_stats(youtube, cid):

    request = youtube.channels().list(
        part='snippet, contentDetails, statistics',
        forUsername=cid
    )
    response = request.execute()

    if 'items' not in response or len(response['items']) == 0:
        raise ValueError("Channel not found or no data available.")
    
    channel_data = response['items'][0]
    data = {
        'Channel_name': channel_data['snippet']['title'],
        'Subscribers': channel_data['statistics']['subscriberCount'],
        'Views': channel_data['statistics']['viewCount'],
        'Total_vids': channel_data['statistics']['videoCount'],
        'upload_id': channel_data['contentDetails']['relatedPlaylists']['uploads']
    }
    return data

def get_video_ids(youtube, play_id):

    video_ids = []
    request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=play_id,
        maxResults=50
    )
    response = request.execute()

    if 'items' not in response:
        raise ValueError("Playlist not found or no data available.")

    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    while next_page_token:
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=play_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')

    return video_ids

#Fetch data for each video in the list of video IDs.
def fetch_video_data(youtube, video_ids):

    extracted_data = []
    for id_chunk in chunk_list(video_ids, 50):
        id_str = ','.join(id_chunk)
        request = youtube.videos().list(
            part="snippet,statistics",
            id=id_str
        )
        response = request.execute()

        if 'items' not in response:
            raise ValueError("No video data found.")

        for item in response['items']:
            video_data = {
                'Title': item['snippet']['title'],
                'Publish_date': item['snippet']['publishedAt'],
                'Descriptions': item['snippet']['description'],
                'Tags': item['snippet'].get('tags', []),
                'Views': item['statistics'].get('viewCount', 0),
                'Likes': item['statistics'].get('likeCount', 0),
                'No_ofComments': item['statistics'].get('commentCount', 0)
            }
            extracted_data.append(video_data)

    return extracted_data

#Split a list into chunks of size n because 50 response
def chunk_list(lst, n):

    for i in range(0, len(lst), n):
        yield lst[i:i + n]

#Store extracted data to a CSV file.
def store_data_to_file(data, filename='youtube_data.csv'):

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print("Data stored to", filename)

def main():
    try:
        api_key = load_credentials()
        youtube = build_youtube_client(api_key)
        
        # Define channel IDs and playlist IDs
        channel_ids = ['id1', 'id2',...]
        playlist_ids = ['id1', 'id2',...]
        #channel_ids, playlist_ids = load_channel_and_playlist_ids()
        
        for channel_id, playlist_id in zip(channel_ids, playlist_ids):
            channel_stats = get_channel_stats(youtube, channel_id)
            print("Channel Stats:", channel_stats)
            
            video_ids = get_video_ids(youtube, playlist_id)
            print("Total Videos Found for Playlist", playlist_id, ":", len(video_ids))
            
            extracted_data = fetch_video_data(youtube, video_ids)
            print("Total Videos Fetched for Playlist", playlist_id, ":", len(extracted_data))
            
            #store data to a file for each channel and playlist
            store_data_to_file(extracted_data, filename=f'{channel_id}_data.csv')
    
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()

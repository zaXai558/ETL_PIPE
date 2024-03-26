from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import pandas as pd

def load_credentials():
    """
    Load API credentials from environment variables.
    """
    load_dotenv()
    api_key = os.getenv("api_key")
    channel_id = os.getenv("channel_id")
    playlist_id = os.getenv("playlist_id")
    
    if not (api_key and channel_id and playlist_id):
        raise ValueError("Please provide valid API credentials.")

    return api_key, channel_id, playlist_id

def build_youtube_client(api_key):
    """
    Build and return a YouTube API client.
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    return youtube

def get_channel_stats(youtube, cid):
    """
    Get statistics for a YouTube channel.
    """
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
    """
    Get video IDs from a playlist.
    """
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

def fetch_video_data(youtube, video_ids):
    """
    Fetch data for each video in the list of video IDs.
    """
    extracted_data = []
    for id_chunk in chunk_list(video_ids, 50):
        id_str = ','.join(id_chunk)
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
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
                'No_ofComments': item['statistics'].get('commentCount', 0),
                'Duration': item['contentDetails']['duration']
            }
            extracted_data.append(video_data)

    return extracted_data

def chunk_list(lst, n):
    """
    Split a list into chunks of size n.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def store_data_to_file(data, filename='youtube_data.csv'):
    """
    Store extracted data to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print("Data stored to", filename)

def main():
    try:
        api_key, channel_id, playlist_id = load_credentials()
        youtube = build_youtube_client(api_key)
        
        channel_stats = get_channel_stats(youtube, channel_id)
        print("Channel Stats:", channel_stats)
        
        video_ids = get_video_ids(youtube, playlist_id)
        print("Total Videos Found:", len(video_ids))
        
        extracted_data = fetch_video_data(youtube, video_ids)
        print("Total Videos Fetched:", len(extracted_data))
        
        store_data_to_file(extracted_data)
    
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()

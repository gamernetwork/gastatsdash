import json

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from Statsdash import config


def get_google_analytics():
    """
    Gets the Google Analytics resource.
    """
    scopes = ['https://www.googleapis.com/auth/analytics.readonly', ]
    credentials = service_account.Credentials.from_service_account_file(
        config.GOOGLE['KEY_FILE'],
        scopes=scopes
    )
    service = build('analytics', 'v3', credentials=credentials)
    return service.data().ga()


def get_youtube_analytics():
    """
    Gets the YouTube Analytics resource.
    """
    credentials = get_youtube_credentials()
    service = build('youtubeAnalytics', 'v2', credentials=credentials)
    return service.reports()


def get_youtube_videos():
    """
    Gets the YouTube Videos resource.
    """
    credentials = get_youtube_credentials()
    service = build('youtube', 'v2', credentials=credentials)
    return service.videos()


def get_youtube_credentials():
    credentials_file = config.YOUTUBE['CREDENTIALS_FILE']
    with open(credentials_file) as json_file:
        data = json.load(json_file)
    return Credentials(**data)

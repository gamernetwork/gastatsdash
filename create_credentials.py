import os

from google_auth_oauthlib.flow import InstalledAppFlow

from Statsdash import config
KEY_FILE = config.YOUTUBE['KEY_FILE']

API_SERVICE_NAME = 'youtubeAnalytics'
API_VERSION = 'v2'
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtubepartner'
]
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

# Authorize the request and store authorization credentials.
flow = InstalledAppFlow.from_client_secrets_file(KEY_FILE, SCOPES)
credentials = flow.run_local_server()
jason = credentials.to_json()

with open(PROJECT_ROOT + '/credentials.json', 'w') as outfile:
    outfile.write(jason)

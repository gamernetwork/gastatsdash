import sys
from oauth2client.tools import argparser, run_flow
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets

from Statsdash.Youtube import config
CLIENT_SECRETS_FILE = config.CLIENT_SECRETS_FILE
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtubepartner"]

flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,scope=" ".join(YOUTUBE_SCOPES),redirect_uri='http://localhost:8080')
storage = Storage("youtube-oauth2.json")
credentials = run_flow(flow, storage)

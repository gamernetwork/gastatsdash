import os
import subprocess

API_SERVICE_NAME = 'youtubeAnalytics'
API_VERSION = 'v2'
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtubepartner'
]
PROJECT_ROOT = dir_path = os.path.dirname(os.path.realpath(__file__))
OUTPUT_LOCATION = PROJECT_ROOT + '/credentials/oauth2.json'
print(PROJECT_ROOT)
print(OUTPUT_LOCATION)

print(' '.join(SCOPES))
subprocess.run([
    'google-oauthlib-tool',
    '--client-secrets',
    '/Users/john/src/gastatsdash/credentials/client_secret_611899013700-ummpb9k80n2ks2c5esvk8oq8bktq1a6e.apps.googleusercontent.com.json',
    '--scope',
    ' '.join(SCOPES),
    '--save',
    '--credentials',
    OUTPUT_LOCATION,
])

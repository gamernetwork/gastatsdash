#!/usr/bin/python

from apiclient.discovery import build
from apiclient.errors import HttpError
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
import httplib2
import logging
import logging.config
import logging.handlers
import os

import Statsdash.utilities as utils
from Statsdash.config import LOGGING
from Statsdash.Youtube import config

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

KEY_FILE = config.KEY_FILE

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtubepartner"
]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_ANALYTICS_API_SERVICE_NAME = "youtubeAnalytics"
YOUTUBE_ANALYTICS_API_VERSION = "v2"
YOUTUBE_PARTNER_API_SERVICE_NAME = "youtubePartner"
YOUTUBE_PARTNER_API_VERSION = "v1"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   KEY_FILE))

with open(config.KEY_FILE, 'rb') as f:
    PRIVATE_KEY = f.read()


class ImproperlyConfiguredException(Exception):
    pass


class Analytics(object):
    """
    Class to retrieve data from the YouTube APIs.
    """
    youtube = None
    youtube_analytics = None
    youtube_partner = None

    def __init__(self):
        """
        Initialise credentials and build api object to query.
        """
        credentials = service_account.Credentials.from_service_account_file(
            config.KEY_FILE,
            scopes=SCOPES
        )
        print('CREDENTIALS')
        print(credentials)
        print(credentials.valid)

        if credentials is None or not credentials.valid:
            raise ImproperlyConfiguredException(
                "Couldn't find any service account credentials. Please run "
                "`python create_credentials.py --noauth_local_webserver` first"
            )
        # NOTE whats happening here? Might be outdated.
        http = credentials.authorize(httplib2.Http())

        self.youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            http=http,
        )
        self.youtube_analytics = build(
            YOUTUBE_ANALYTICS_API_SERVICE_NAME,
            YOUTUBE_ANALYTICS_API_VERSION,
            http=http,
        )
        self.youtube_partner = build(
            YOUTUBE_PARTNER_API_SERVICE_NAME,
            YOUTUBE_PARTNER_API_VERSION,
            http=http,
        )

    def execute_query(self, query):
        """
        Try to execute the API query.
        """
        try:
            results = query.execute()
            return results
        except HttpError as e:
            logger.warning(
                "HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
            )

    def data_available(self, id, date):
        # TODO add docstring
        analytics_query_response = self.youtube_analytics.reports().query(
            ids="contentOwner==%s" % config.CONTENT_OWNER_ID,
            metrics="views",
            dimensions=None,
            startDate=date,
            endDate=date,
            filters="channel==%s" % id,
            maxResults=None,
            sort=None,
        )
        results = self.execute_query(analytics_query_response)
        return 'rows' in results.keys()

    def get_content_owner(self):
        """
        Returns info on the content owner.
        Returns a dictionary, use ["items"][0]["id"] to get the content owner
        id.
        """
        # TODO improve docstring
        contentOwnersService = self.youtube_partner.contentOwners()
        content_owner_doc = contentOwnersService.list(fetchMine=True)
        return self.execute_query(content_owner_doc)

    def get_channel_id(self):
        """
        Returns channel list owned by the content owner.
        """
        # TODO method name and docstring ambiguous.
        channels_list_response = self.youtube.channels().list(
            managedByMe=True,
            onBehalfOfContentOwner=config.CONTENT_OWNER_ID,
            part="snippet,contentDetails, contentOwnerDetails"
        )
        return self.execute_query(channels_list_response)

    def get_stats(self, id):
        # TODO add docstring.
        subs = self.youtube.channels().list(
            part="statistics",
            id=id,
        )
        return self.execute_query(subs)['items']

    def rollup_stats(self, ids):
        # TODO add docstring
        id_combo = ",".join(ids)
        results = self.get_stats(id_combo)
        stats = {}
        for row in results:
            row["statistics"] = utils.convert_to_floats(
                row["statistics"],
                row["statistics"].keys()
            )
            for key in row['statistics']:
                try:
                    stats[key] += row["statistics"][key]
                # TODO don't use KeyError, just check if key in dict?
                except:
                    stats[key] = row["statistics"][key]
        return stats

    def run_analytics_report(self, start_date, end_date, metrics, dimensions,
                             filters, max_results=None, sort=None):
        """
        run a query on youtube analytics
        returns response with data in response['rows']

        rows :list contains all rows of the result table. Each item in the list
        is an array that contains comma-delimited data corresponding to a
        single row of data, ordered by order specified in query.
        """
        analytics_query_response = self.youtube_analytics.reports().query(
            ids="contentOwner==%s" % config.CONTENT_OWNER_ID,
            metrics=metrics,
            dimensions=dimensions,
            startDate=start_date,
            endDate=end_date,
            filters=filters,
            maxResults=max_results,
            sort=sort,
            fields="rows,kind,columnHeaders",
        )
        result = self.execute_query(analytics_query_response)
        return result

    def rollup_ids(self, ids, start, end, metrics,
                   dimensions=None, filters=None, sort=None, max_results=None,
                   aggregate_key=None):
        # TODO docstring
        # TODO this shouldn't be called main_row
        main_row = []
        for id in ids:
            if filters:
                filter = filters + ";channel==%s" % id
            else:
                filter = "channel==%s" % id
            # TODO use **kwargs?
            results = self.run_analytics_report(
                start, end, metrics=metrics, dimensions=dimensions,
                filters=filter, max_results=max_results, sort=sort
            )
            rows = utils.format_data_rows(results)
            if rows:
                for row in rows:
                    row = utils.convert_to_floats(row, metrics.split(","))
                # NOTE whats happening here?
                main_row.extend(rows)
            else:
                # TODO f string
                logger.debug(f'No data for {id} on {start} - {end}')
        main_row = utils.aggregate_data(
            main_row,
            metrics.split(","),
            aggregate_key
        )
        return main_row

    def get_video(self, id):
        """
        Returns info on video with specified id.
        """
        video_results = self.youtube.videos().list(
            id=id,
            part="snippet"
        )
        return self.execute_query(video_results)

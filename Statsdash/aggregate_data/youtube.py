from pprint import pprint
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .base import AggregateData
from Statsdash.analytics import YouTubeAnalytics, YouTubeVideos, our_metrics
from Statsdash.utils import utils
from Statsdash.Youtube import config


API_SERVICE_NAME = 'youtubeAnalytics'
API_VERSION = 'v2'


SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtubepartner'
]
with open(config.CREDENTIALS_FILE) as json_file:
    data = json.load(json_file)
credentials = Credentials(**data)

service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
resource = service.reports()

service = build('youtube', 'v3', credentials=credentials)
videos = service.videos()
youtube_videos = YouTubeVideos(videos)


Dimensions = YouTubeAnalytics.Dimensions
Metrics = YouTubeAnalytics.Metrics


class YouTubeData(AggregateData):

    analytics = YouTubeAnalytics(resource, config.CONTENT_OWNER_ID)
    site_ids = config.CHANNELS


    # def check_available_data(self):
    #     run_report = {"result": True, "channel": []}
    #     for channel in self.channels:
    #         ids = self.channel_ids[channel]
    #         for id in ids:
    #             data_available = analytics.data_available(id, self.period.get_end())
    #             if not data_available:
    #                 run_report['result'] = False
    #                 run_report['channel'].append(channel)
    #     return run_report


class ChannelSummaryData(YouTubeData):
    table_label = 'summary_table'
    metrics = [
        Metrics.estimated_minutes_watched,
        Metrics.subscribers_gained,
        Metrics.subscribers_lost,
    ]
    extra_metrics = [
        'subscriber_change'
    ]
    # sort_by = '-' + Metrics.estimated_minutes_watched[0]
    match_key = Dimensions.channel[1]

    # TODO consider changing site/channel to property
    def _get_extra_data(self, period, site, data):
        for item in data:
            item['subscriber_change'] = \
                item['subscribersGained'] - item['subscribersLost']
            item['channel'] = site
        return data


class ChannelStatsData(YouTubeData):
    table_label = 'stats_table'
    metrics = [
        Metrics.views,
        Metrics.likes,
        Metrics.dislikes,
        Metrics.comments,
        Metrics.shares,
        Metrics.subscribers_gained,
    ]
    extra_metrics = [
        'like_rate',
        'comment_rate',
        'shares_rate',
        'subs_rate',
        'like_ratio',
        'dislike_ratio',
    ]
    sort_rows_by = Metrics.views
    match_key = Dimensions.channel[1]

    # TODO how to handle rates?

    def _get_extra_data(self, period, site, data):
        # TODO clean
        # TODO use constants
        for item in data:
            item['channel'] = site
            item['like_rate'] = utils.rate_per_1000(item['likes'], item['views'])
            item['comment_rate'] = utils.rate_per_1000(item['comments'], item['views'])
            item['shares_rate'] = utils.rate_per_1000(item['shares'], item['views'])
            item['subs_rate'] = utils.rate_per_1000(item['subscribersGained'], item['views'])
            try:
                item['like_ratio'] = utils.sig_fig(2, item['likes'] / item['dislikes'])
            except ZeroDivisionError:
                item['like_ratio'] = 0
            try:
                item['dislike_ratio'] = utils.sig_fig(2, item['dislikes'] / item[
                    'dislikes'])
            except ZeroDivisionError:
                item['dislike_ratio'] = 0
        return data


class CountryData(YouTubeData):
    table_label = 'geo_table'
    metrics = [
        Metrics.views,
        Metrics.estimated_minutes_watched,
        Metrics.subscribers_gained,
        Metrics.subscribers_lost,
    ]
    extra_metrics = [
        'subscriber_change',
    ]
    dimensions = [
        Dimensions.country
    ]
    sort_by = '-' + Metrics.estimated_minutes_watched[0]
    aggregate_key = Dimensions.country[0]
    match_key = Dimensions.country[1]
    limit = 20

    def _get_extra_data(self, period, site, data):
        for item in data:
            item['subscriber_change'] = \
                item[Metrics.subscribers_gained[0]] - item[Metrics.subscribers_lost[0]]
        return data

    def _aggregate_data(self, data):
        # TODO some sort of extra metrics thing would be cool.
        return utils.aggregate_data(
            data,
            our_metrics(self.metrics) + ['subscriber_change'],
            match_key=self.match_key
        )


class VideoData(YouTubeData):
    table_label = 'top_vids'
    metrics = [
        Metrics.views,
        Metrics.estimated_minutes_watched,
    ]

    dimensions = [
        Dimensions.video,
    ]
    extra_params = {'maxResults': 20}

    # NOTE you need to sort by descending views if you want to run a
    # `dimensions=video` report, and you can only retrieve at most 200 results
    sort_by = '-' + Metrics.views[0]
    aggregate_key = Dimensions.video[0]
    match_key = Dimensions.video[1]

    def _get_extra_data(self, period, site, data):
        for item in data:
            item['title'] = self._get_video_title(item['video'])
            item['channel'] = site
        return data

    def _get_video_title(self, _id):
        video_info = youtube_videos.get_video(_id)
        try:
            return video_info['items'][0]['snippet']['title']
        except IndexError:
            return 'Video Not Found'


class TrafficSourceData(YouTubeData):
    table_label = 'traffic'
    metrics = [
        Metrics.estimated_minutes_watched,
    ]
    dimensions = [
        Dimensions.insight_traffic_source_type
    ]
    source_types = [
        'ANNOTATION', 'EXT_URL', 'NO_LINK_OTHER', 'NOTIFICATION',
        'PLAYLIST', 'RELATED_VIDEO', 'SUBSCRIBER', 'YT_CHANNEL',
        'YT_OTHER_PAGE', 'YT_PLAYLIST_PAGE', 'YT_SEARCH',
    ]
    aggregate_key = Dimensions.insight_traffic_source_type[0]
    match_key = Dimensions.insight_traffic_source_type[1]

    def _get_extra_data(self, period, site, data):
        channel_total = 0.0
        for item in data:
            item['channel'] = site
            channel_total += item['estimatedMinutesWatched']
        for item in data:
            item['channel_total'] = channel_total
        return data

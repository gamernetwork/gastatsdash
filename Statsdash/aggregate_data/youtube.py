from .base import AggregateData
from Statsdash import config
from Statsdash.analytics import YouTubeAnalytics, YouTubeVideos
from Statsdash.resources import get_youtube_videos
from Statsdash import utils

CONTENT_OWNER_ID = config.YOUTUBE['CONTENT_OWNER_ID']
TABLES = config.YOUTUBE['CHANNELS']


Dimensions = YouTubeAnalytics.Dimensions
Metrics = YouTubeAnalytics.Metrics


class YouTubeData(AggregateData):

    def __init__(self, resource, sites, period, frequency):
        super().__init__(sites, period, frequency)
        self.analytics = YouTubeAnalytics(resource, CONTENT_OWNER_ID)
        self.site_ids = TABLES


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
    sort_by = Metrics.estimated_minutes_watched
    match_key = Dimensions.channel

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
    match_key = Dimensions.channel

    def _get_extra_data(self, period, site, data):
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
    sort_by = Metrics.estimated_minutes_watched
    aggregate_key = Dimensions.country
    match_key = Dimensions.country
    limit = 20

    def _get_extra_data(self, period, site, data):
        for item in data:
            item['subscriber_change'] = \
                item[Metrics.subscribers_gained[0]] - item[Metrics.subscribers_lost[0]]
        return data


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
    sort_by = Metrics.views
    aggregate_key = Dimensions.video
    match_key = Dimensions.video
    videos_method = get_youtube_videos

    def _get_extra_data(self, period, site, data):
        for item in data:
            item['title'] = self._get_video_title(item['video'])
            item['channel'] = site
        return data

    def _get_video_title(self, _id):
        self.videos = YouTubeVideos(get_youtube_videos())
        video_info = self.videos.get_video(_id)
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
    aggregate_key = Dimensions.insight_traffic_source_type
    match_key = Dimensions.insight_traffic_source_type

    def _get_extra_data(self, period, site, data):
        channel_total = 0.0
        for item in data:
            item['channel'] = site
            channel_total += item['estimatedMinutesWatched']
        for item in data:
            item['channel_total'] = channel_total
        return data


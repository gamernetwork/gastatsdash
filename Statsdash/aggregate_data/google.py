from pprint import pprint
from .base import AggregateData
from Statsdash.analytics import GoogleAnalytics, third_party_metrics
from Statsdash import config, utils

TABLES = config.GOOGLE['TABLES']
Metrics = GoogleAnalytics.Metrics
Dimensions = GoogleAnalytics.Dimensions
Countries = GoogleAnalytics.Countries


class AnalyticsData(AggregateData):

    def __init__(self, resource, sites, period, frequency):
        super().__init__(sites, period, frequency)
        self.analytics = GoogleAnalytics(resource)
        self.site_ids = get_site_ids()


class SummaryData(AnalyticsData):
    """
    Gets the aggregated analytics data for all sites.
    """
    table_label = 'summary_table'
    metrics = [
        Metrics.pageviews,
        Metrics.users,
        Metrics.sessions,
        Metrics.pv_per_sessions,
        Metrics.avg_session_time,
    ]

    def _format_data(self, data, site):
        data = super()._format_data(data, site)
        return self._apply_averages(data)

    # TODO This could be handled in the template.
    def _apply_averages(self, data):
        """
        Get average for metrics which are averages.

        Args:
            * `data` - `dict` - analytics data blob (after rename).

        Returns:
            * `dict`
        """
        len_sites = len(self.sites)
        av = data.get(Metrics.pv_per_sessions[1], 0) / len_sites
        data[Metrics.pv_per_sessions[1]] = av
        av = data.get(Metrics.avg_session_time[1], 0) / len_sites / 60.0
        data[Metrics.avg_session_time[1]] = av
        return data


class SiteSummaryData(AnalyticsData):

    table_label = 'site_table'
    metrics = [
        Metrics.pageviews,
        Metrics.users,
        Metrics.sessions,
        Metrics.pv_per_sessions,
        Metrics.avg_session_time,
    ]

    match_key = 'site'
    sort_rows_by = Metrics.users

    def _format_data(self, data, site):
        data = super()._format_data(data, site)
        # Maybe we could add this by default?
        data['site'] = site
        return data


class ArticleData(AnalyticsData):

    table_label = 'top_articles'
    metrics = [
        Metrics.pageviews,
    ]
    dimensions = [
        Dimensions.title,
        Dimensions.path,
        Dimensions.host,
    ]
    filters = 'ga:pagePathLevel1!=/;ga:pagePath!~/page/*;ga:pagePath!~^/\?.*'
    sort_by = Metrics.pageviews
    match_key = 'site_path'
    aggregate_key = Dimensions.path
    limit = 20

    def _format_data(self, data, site):
        data = super()._format_data(data, site)

        path = data['path']
        title = data['title']

        new_path = utils.remove_query_string(path)
        new_title = utils.add_amp_to_title(path, title)

        data['path'] = new_path
        data['site_path'] = site + new_path
        data['title'] = new_title
        return data


class CountryData(AnalyticsData):

    table_label = 'geo_table'
    metrics = [
        Metrics.pageviews,
        Metrics.users,
    ]
    dimensions = [
        Dimensions.country,
    ]
    countries = [
        Countries.czech_republic,
        Countries.germany,
        Countries.denmark,
        Countries.spain,
        Countries.france,
        Countries.italy,
        Countries.portugal,
        Countries.sweden,
        Countries.poland,
        Countries.brazil,
        Countries.belgium,
        Countries.netherlands,
        Countries.united_kingdom,
        Countries.ireland,
        Countries.united_states,
        Countries.canada,
        Countries.australia,
        Countries.new_zealand,
    ]

    countries_regex = "|".join(countries)
    filters = f'ga:country=~{countries_regex}'
    rest_of_world_filters = f'ga:country!~{countries_regex}'
    sort_by = Metrics.pageviews
    sort_rows_by = Metrics.users
    aggregate_key = Dimensions.country
    match_key = Dimensions.country

    def _get_extra_data(self, period, site, data):
        world_rows = self.analytics.get_data(
            self.site_ids[site],
            period.get_start(),
            period.get_end(),
            metrics=third_party_metrics(self.metrics),
            dimensions=None,
            filters=self.rest_of_world_filters,
            sort=self.sort_by[0],
            aggregate_key=None
        )
        if world_rows:
            world_rows[0]['ga:country'] = 'ROW'
        else:
            world_rows = [{'ga:country': 'ROW', 'ga:pageviews': 0, 'ga:users': 0}]
        data.extend(world_rows)
        return data


class TrafficSourceData(AnalyticsData):

    table_label = 'traffic_table'
    metrics = [
        Metrics.pageviews,
        Metrics.users,
    ]
    dimensions = [
        Dimensions.source,
    ]
    sort_by = Metrics.users
    sort_rows_by = Metrics.users
    aggregate_key = Dimensions.source
    match_key = Dimensions.source
    limit = 10


class DeviceData(AnalyticsData):

    table_label = 'device_table'
    metrics = [
        Metrics.users,
    ]
    dimensions = [
        Dimensions.device_category,
    ]
    sort_by = Metrics.users
    sort_rows_by = Metrics.users
    aggregate_key = Dimensions.device_category
    match_key = Dimensions.device_category


class SocialData(AnalyticsData):

    metrics = [
        Metrics.pageviews,
        Metrics.users,
        Metrics.sessions,
    ]
    dimensions = [
        Dimensions.social_network,
    ]

    filters = 'ga:socialNetwork!=(not set)'
    sort_by = Metrics.users
    aggregate_key = Dimensions.social_network
    match_key = Dimensions.social_network
    limit = 15


def get_site_ids():
    # NOTE this method exists so it can be easily mocked during tests.
    return TABLES

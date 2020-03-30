
from google.oauth2 import service_account
from googleapiclient.discovery import build

from .base import AggregateData
from Statsdash.analytics import GoogleAnalytics, third_party_metrics
from Statsdash.utils import utils
from Statsdash import config

API_SERVICE_NAME = 'analytics'
API_VERSION = 'v3'

KEY_FILE = config.GOOGLE['KEY_FILE']
TABLES = config.GOOGLE['TABLES']

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly', ]
credentials = service_account.Credentials.from_service_account_file(
    KEY_FILE,
    scopes=SCOPES
)
# TODO should be initialized outside of main script?
service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
resource = service.data().ga()

Metrics = GoogleAnalytics.Metrics
Dimensions = GoogleAnalytics.Dimensions
Countries = GoogleAnalytics.Countries


def get_site_ids():
    return TABLES


class AnalyticsData(AggregateData):

    analytics = GoogleAnalytics(resource)

    def __init__(self, sites, period, frequency):
        super().__init__(sites, period, frequency)
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

    # TODO I wonder if this should be happening here.
    def _apply_averages(self, data):
        """
        Get average for metrics which are averages.

        Args:
            * `data` - `dict` - analytics data blob (after rename).

        Returns:
            * `dict`
        """
        len_sites = len(self.sites)
        # TODO metrics could be turned into classes. Each class could handle average.
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
    # TODO clean up sort_by
    sort_by = Metrics.pageviews
    match_key = 'site_path'
    aggregate_key = Dimensions.path

    def _format_data(self, data, site):
        data = super()._format_data(data, site)

        # TODO clean logic
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
            sort=self.sort_by,
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


# TODO social chart should be different form the data class. should be in different module
# NOTE gets period for every day between start and finish

#     def social_chart(self):
#
#         current = self.period.start_date
#         end = self.period.end_date
#         dates = []
#         while current <= end:
#             current_range = utils.StatsRange("day", current, current)
#             dates.append(current_range)
#             current = current + timedelta(days=1)
#
#         data = {}
#         network_data = {}
#         for count, date in enumerate(dates):
#             social = []
#             network_social = []
#             metrics = "ga:pageviews,ga:users,ga:sessions"
#             for site in config.TABLES.keys():
#                 rows = [analytics.rollup_ids(self.site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions=None, filters="ga:socialNetwork!=(not set)", sort="-ga:users")]
#                 if rows[0]:
#                     rows = self._remove_ga_names(rows)
#                     for row in rows:
#                         row = utils.convert_to_floats(row, ["pageviews", "users", "sessions"])
#                     if site in self.sites:
#                         social.extend(rows)
#                     network_social.extend(rows)
#                 else:
#                     logger.debug("No data for site " + site + " on " + date.get_start() + " - " + date.get_end())
#
#             aggregate = utils.aggregate_data(social, ["pageviews", "users", "sessions"])
#             network_aggregate = utils.aggregate_data(network_social, ["pageviews", "users", "sessions"])
#
#             data[date.get_start()] = aggregate
#             network_data[date.get_start()] = network_aggregate
#
#         x_labels = []
#         graph_data = {"users": [], "pageviews": [], "network_pageviews": [], "network_users": []}
#         for range in dates:
#             x_labels.append(range.get_start())
#             graph_data["users"].append(data[range.get_start()]["users"])
#             graph_data["pageviews"].append(data[range.get_start()]["pageviews"])
#             graph_data["network_users"].append(network_data[range.get_start()]["users"])
#             graph_data["network_pageviews"].append(network_data[range.get_start()]["pageviews"])
#
#         chart = utils.chart("Social Data", x_labels, graph_data, "Day", "Number")
#         return chart


# TODO This should work like social chart. should be in different module
#     def device_chart(self, data):
#         chart_data = {}
#         x_labels = []
#         for count, row in enumerate(data):
#             for device in row["data"]:
#                 try:
#                     chart_data[device["device_category"]].append(utils.percentage(device["users"], row["summary"]["users"]))
#                 except KeyError:
#                     chart_data[device["device_category"]] = [utils.percentage(device["users"], row["summary"]["users"])]
#
#             x_labels.append(row["month"])
#
#         chart = utils.chart("Device Chart", x_labels, chart_data, "Month", "Percentage of Users")
#         return chart


# TODO This is a composite table
# def referring_sites_table(self, num_articles):
#     # gets the data
#     sources = self._get_by_source()[:5]
#     referrals = []
#     black_ex = '|'
#     black_string = black_ex.join(config.SOURCE_BLACK_LIST)
#     regex = re.compile(black_string)
#     for row in sources:
#         source = row["source"]
#         match = regex.search(source)
#         if match:
#             continue
#         else:
#             filter = "ga:source==%s" % source
#             article = self.referral_articles(filter, num_articles)
#             row["source"] = source
#             row["articles"] = article
#             referrals.append(row)
#     return referrals

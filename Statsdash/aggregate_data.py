from pprint import pprint
from datetime import datetime, timedelta
from html.parser import HTMLParser
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging.config
import logging.handlers
import re

from Statsdash.analytics import GoogleAnalytics, google_metrics, our_metrics
from Statsdash.GA import config
from Statsdash.utils import utils
from Statsdash.config import LOGGING
from Statsdash.stats_range import StatsRange

# TODO move this somewhere else?
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly', ]
credentials = service_account.Credentials.from_service_account_file(
    config.KEY_FILE,
    scopes=SCOPES
)
service = build('analytics', 'v3', credentials=credentials)
resource = service.data().ga()

analytics = GoogleAnalytics(resource)

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

Metrics = GoogleAnalytics.Metrics
Dimensions = GoogleAnalytics.Dimensions
Countries = GoogleAnalytics.Countries


class AnalyticsData:

    metrics = []
    dimensions = []
    aggregate_key = None
    filters = None
    match_key = None
    sort_by = None
    sort_rows_by = None
    limit = None

    def __init__(self, site_tables, period, frequency):
        self.sites = site_tables.keys()
        self.frequency = frequency
        # TODO pass name into get_pervious_period
        previous_period = StatsRange.get_previous_period(period, self.frequency)  # remove literal
        previous_period.name = 'previous'
        yearly_period = StatsRange.get_previous_period(period, "YEARLY")
        yearly_period.name = 'yearly'
        self.periods = [period, previous_period, yearly_period]
        # TODO rename attribute
        self.site_ids = site_tables

    # TODO test
    def get_table(self):
        """

        """
        period_data = []
        for period in self.periods:
            data = self._get_data_for_period(period)
            period_data.append(data)

        if self.limit:
            return self._join_periods(period_data)
        return self._join_periods(period_data)

    def _join_periods(self, data):
        """
        Gets the data for each period and combines them into a single dict.

        Args:
            * `data` - `list` - an executed query for each period.

        Returns:
            * `dict`
        """
        # each item in data is a period of data
        current_period = data[0]
        other_periods = data[1:]
        new_data = []
        #iterate over every item in the current period and get the change versus prevous periods
        for i, current_period_data in enumerate(current_period):
            joined_data = current_period_data
            for j, other_period in enumerate(other_periods, 1):
                period = self.periods[j]
                other_period_data = other_period[i]
                change = utils.get_change(
                    current_period_data,
                    other_period_data,
                    our_metrics(self.metrics),
                    match_key=self.match_key
                )
                change = utils.prefix_keys(change, period.name + '_')
                joined_data.update(change)
            new_data.append(joined_data)
        return new_data

    def _get_data_for_period(self, period):
        """
        Gets the analytics data for each site in `self.site_ids` for the given
        period and prepares it for the table: renames the keys for each metric,
        aggregates the data for each site, and gets the average for values
        where appropriate.

        Args:
            * `period` - `StatsRange`

        Returns:
            * `list` - data for each site.
        """
        all_sites_data = []
        for site in self.sites:
            data = analytics.get_data(
                self.site_ids[site],
                period.get_start(),
                period.get_end(),
                # TODO rename method.
                metrics=','.join(google_metrics(self.metrics)),
                dimensions=','.join(google_metrics(self.dimensions)),
                filters=self.filters,
                sort=self.sort_by,
                aggregate_key=self.aggregate_key,
            )
            data = self._get_extra_data(period, site, data)

            # data is a list with a dict for each id in site config
            if data:
                data = self._format_all_data(data, site)
                all_sites_data = all_sites_data + data
            else:
                logger.debug(
                    f'No data for site {site} on {period.get_start()} - '
                    f'{period.get_end()}'
                )
        data = self._aggregate_data(all_sites_data)
        if self.sort_rows_by:
            data = utils.sort_data(data, self.sort_rows_by[1])
        if self.limit:
            data = data[:self.limit]
        return data

    def _get_extra_data(self, period, site, data):
        """

        """
        # TODO docstring
        return data

    def _aggregate_data(self, data):
        return utils.aggregate_data(
            data,
            our_metrics(self.metrics),
            match_key=self.match_key
        )

    def _format_all_data(self, data, site):
        output = []
        for item in data:
            item = self._format_data(item, site)
            output.append(item)
        return output

    def _format_data(self, data, site):
        replacements = [(c[0], c[1]) for c in self.metrics + self.dimensions]
        data = utils.change_key_names(data, replacements)
        return data

    def _remove_query_string(self, path):
        """
        Removes any queries attached to the end of a page path, so aggregation
        can be accurate.
        """
        # TODO finish docstring
        # NOTE not sure why linter is compaining. Maybe `r`?
        exp = "^([^\?]+)\?.*"
        regex = re.compile(exp)
        m = regex.search(path)
        if m:
            new_path = regex.split(path)[1]
            return new_path
        else:
            return path

    def _get_title(self, path, title):
        """
        Checks if the article path includes 'amp' making it an AMP article, and
        appends this to the name so easier to see in report.
        """
        # TODO finish docstring
        # NOTE title/docstring confusion
        exp = "/amp/"
        regex = re.compile(exp)
        m = regex.search(path + "/")
        if m:
            title = title + " (AMP)"
            # amp articles come with html characters
            h = HTMLParser()
            title = h.unescape(title)
        return title


class SummaryData(AnalyticsData):
    """
    Gets the aggregated analytics data for all sites.
    """
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


    # TODO look closely at this method.
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

    metrics = [
        Metrics.pageviews,
        Metrics.users,
        Metrics.sessions,
        Metrics.pv_per_sessions,
        Metrics.avg_session_time,
    ]

    match_key = 'site'

    def _format_data(self, data, site):
        data = super()._format_data(data, site)
        # Maybe we could add this by default?
        data['site'] = site
        return data

    # TODO replace with simple sort_by attribute.
    def _get_data_for_period(self, period):
        # sort sites by users
        data = super()._get_data_for_period(period)
        return utils.sort_data(data, Metrics.users[1])


class ArticleData(AnalyticsData):

    metrics = [
        Metrics.pageviews,
    ]
    dimensions = [
        Dimensions.title,
        Dimensions.path,
        Dimensions.host,
    ]
    filters = 'ga:pagePathLevel1!=/;ga:pagePath!~/page/*;ga:pagePath!~^/\?.*'
    sort_by = '-' + Metrics.pageviews[0]
    # TODO double check sorting
    match_key = 'site_path'
    aggregate_key = Dimensions.path[0]

    def _format_data(self, data, site):
        data = super()._format_data(data, site)

        # TODO clean logic
        path = data['path']
        title = data['title']
        new_path = self._remove_query_string(path)
        new_title = self._get_title(path, title)
        data['path'] = new_path
        data['site_path'] = site + new_path
        data['title'] = new_title
        return data


class CountryData(AnalyticsData):

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
    match_key = 'country'
    sort_by = '-' + Metrics.pageviews[0]
    sort_rows_by = Metrics.users
    aggregate_key = Dimensions.country[0]

    def _get_extra_data(self, period, site, data):
        world_rows = analytics.get_data(
            self.site_ids[site],
            period.get_start(),
            period.get_end(),
            metrics=','.join(google_metrics(self.metrics)),
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

    metrics = [
        Metrics.pageviews,
        Metrics.users,
    ]
    dimensions = [
        Dimensions.source,
    ]
    sort_by = '-' + Metrics.users[0]
    sort_rows_by = Metrics.users
    aggregate_key = Dimensions.source[0]
    match_key = Dimensions.source[1]
    limit = 10


class DeviceData(AnalyticsData):

    metrics = [
        Metrics.users,
    ]
    dimensions = [
        Dimensions.device_category,
    ]
    sort_by = '-' + Metrics.users[0]
    sort_rows_by = Metrics.users
    aggregate_key = Dimensions.device_category[0]
    match_key = Dimensions.device_category[1]


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
    sort_by = '-' + Metrics.users[0]
    aggregate_key = Dimensions.social_network[0]
    match_key = Dimensions.social_network[1]
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



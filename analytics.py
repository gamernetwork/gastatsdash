from collections import OrderedDict

from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
from apiclient.discovery import build

import config

def get_analytics():
    with open(config.KEY_FILE) as f:
        private_key = f.read()
    analytics = Analytics(config.CLIENT_EMAIL, private_key)
    return analytics

class Analytics(object):
    """
    GN google analytics object for retrieving pertinent GA data.
    """

    def __init__(self, email, key):
        credentials = SignedJwtAssertionCredentials(email, key,
            'https://www.googleapis.com/auth/analytics.readonly')
        http_auth = credentials.authorize(Http())
        ga_service = build('analytics', 'v3', http=http_auth)
        self.ga = ga_service.data().ga()

    def _format_article_breakdown_results(self, results):
        try:
            result_rows =  results['rows']
        except KeyError:
            result_rows = []
        article_data = OrderedDict()
        for row in result_rows:
            title, path, host, pageviews = row
            article_data[path] = {
                'title': title,
                'path': path,
                'host': host,
                'pageviews': int(pageviews)
            }
        return article_data

    def data_available_for_site(self, site_id, stats_date):
        query = self.ga.get(
            ids=site_id,
            start_date=stats_date,
            end_date=stats_date,
            metrics="ga:pageviews",
            dimensions="ga:dateHour",
        )
        results = query.execute()
        try:
            data_available = len(results['rows']) == 24
        except KeyError:
            return False
        return data_available

    def get_article_breakdown(self, site_id, stats_range, 
            topic=None, min_pageviews=1):
        """
        Get pageview breakdown grouped by articles for a particular stats daterange
        and topic (optional).
        """
        start_date = stats_range.get_start()
        end_date = stats_range.get_end()
        filters = ''
        if topic:
            filters = 'ga:dimension2=@%s;' % topic
        filters += 'ga:pageviews>%s' % min_pageviews
        query = self.ga.get(
            ids=site_id,
            start_date=start_date,
            end_date=end_date,
            sort='-ga:pageviews',
            metrics='ga:pageviews',
            dimensions='ga:pageTitle,ga:pagePath,ga:hostname',
            filters=filters,
        )
        results = query.execute()
        article_data = self._format_article_breakdown_results(results)
        return article_data

    def get_article_breakdown_two_periods(self, site_id, first_period, 
            second_period, topic=None, min_pageviews=1):
        """
        """
        first_data = self.get_article_breakdown(site_id, first_period, 
            topic=topic, min_pageviews=min_pageviews)
        second_data = self.get_article_breakdown(site_id, second_period, 
            topic=topic, min_pageviews=min_pageviews)
        for path, article_info in first_data.items():
            try:
                previous_period_pageviews = second_data[path]['pageviews']
            except KeyError:
                previous_period_pageviews = 0
            article_info['previous_pageviews'] = previous_period_pageviews
            article_info['change'] = article_info['pageviews'] - previous_period_pageviews
        return first_data


class StatsRange(object):
    
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def _get_formatted_date(self, d):
        return d.isoformat()

    def get_start(self):
        return self._get_formatted_date(self.start_date)

    def get_end(self):
        return self._get_formatted_date(self.end_date)


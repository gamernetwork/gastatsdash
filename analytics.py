from datetime import timedelta
from collections import OrderedDict

from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
from apiclient.discovery import build

import config
from dateutils import subtract_one_month

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
            # Changed page titles will lead to duplicate rows
            # So, firstly try to increment pageviews on the article we have
            # And then add it to the structure if necessary
            try:
                article_data[path]['pageviews'] += int(pageviews)
            except KeyError:
                article_data[path] = {
                    'title': title,
                    'path': path,
                    'host': host,
                    'pageviews': int(pageviews)
                }
        return article_data

    def _cast_formatted_row(self, formatted_row):
        integer_metrics = ['pageviews', 'visitors']
        for key in integer_metrics:
            try:
                formatted_row[key] = int(formatted_row[key])
            except KeyError:
                continue
        return formatted_row
            

    def _format_results_flat(self, results, keys):
        """
        Given a list of result rows and a list of corresponding key labels, 
        unpack the results in to a list of dictionaries.
        """
        formatted_results = []
        for row in results['rows']:
            key_value_pairs = zip(keys, row)
            formatted_row = dict(key_value_pairs)
            formatted_row = self._cast_formatted_row(formatted_row)
            formatted_results.append(formatted_row)
        return formatted_results

    def _format_results_grouped(self, results, keys, grouping_key):
        """
        Given a list of result rows and a list of corresponding key labels, 
        unpack the results in to an OrderedDict of dictionaries.  The resulting
        OrderedDict has keys based on the grouping_key.
        """
        formatted_results = OrderedDict()
        for row in results['rows']:
            key_value_pairs = zip(keys, row)
            formatted_row = dict(key_value_pairs)
            formatted_row = self._cast_formatted_row(formatted_row)
            formatted_results[formatted_row[grouping_key]] = formatted_row
        return formatted_results

    def data_available_for_site(self, site_id, stats_date):
        # TODO: Persist these results in a cache so we don't smash our rate limit
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

    def _execute_stats_query(self, site_id, stats_range, metrics, sort=None, dimensions=None, filters=None):
        """
        """
        kwargs = {
            'ids': site_id,
            'start_date': stats_range.get_start(),
            'end_date': stats_range.get_end(),
            'metrics': metrics,
        }
        if sort:
            kwargs['sort'] = sort
        if dimensions:
            kwargs['dimensions'] = dimensions
        if filters:
            kwargs['filters'] = filters
        query = self.ga.get(**kwargs)
        return query.execute()

    def get_article_breakdown(self, site_id, stats_range, 
            extra_filters="", min_pageviews=1):
        """
        Get pageview breakdown grouped by articles for a particular stats daterange
        and extra_filters (optional).
        """
        
        black_list = ["/forum", "/messages/updates", "/mods", "/accounts", "/page"]                
        filter_list= 'ga:pagePathLevel1!=/'
        for i in black_list:
        	filter_list += ';ga:pagePath!=%s' %i
        	
        filters = ''        	
        if extra_filters:
            filters = '%s;' % extra_filters
        results = self._execute_stats_query(site_id=site_id, 
            stats_range=stats_range,
            metrics='ga:pageviews',
            sort='-ga:pageviews',
            dimensions='ga:pageTitle,ga:pagePath,ga:hostname',
            filters = filter_list )
        article_data = self._format_article_breakdown_results(results)
        return article_data

    def get_article_breakdown_two_periods(self, site_id, first_period, 
            second_period, extra_filters="", min_pageviews=1):
        """
        """
        first_data = self.get_article_breakdown(site_id, first_period, 
            extra_filters=extra_filters, min_pageviews=min_pageviews)
        second_data = self.get_article_breakdown(site_id, second_period, 
            extra_filters=extra_filters, min_pageviews=min_pageviews)
        for path, article_info in first_data.items():
            try:
                previous_period_pageviews = second_data[path]['pageviews']
            except KeyError:
                previous_period_pageviews = 0
            article_info['previous_pageviews'] = previous_period_pageviews
            article_info['change'] = article_info['pageviews'] - previous_period_pageviews
        return first_data

    def get_site_totals_for_period(self, site_id, stats_range, 
            extra_filters=""):
        """
        Get total pageviews and visitors for a period for a given site.
        """
        filters = ''
        if extra_filters:
            filters = '%s;' % extra_filters
        results = self._execute_stats_query(site_id=site_id, 
            stats_range=stats_range,
            metrics='ga:pageviews,ga:visitors',
            filters=filters)
        try:
            formatted_results = self._format_results_flat(results, ['pageviews', 'visitors'])
        except KeyError:
            formatted_results = [{'visitors': 0, 'pageviews': 0}]
        return formatted_results

    def get_country_breakdown_for_period(self, site_id, stats_range, 
            countries, extra_filters=""):
        countries_regex = '|'.join(countries)
        filters = 'ga:country=~%s' % countries_regex
        if extra_filters:
            filters = '%s;' % extra_filters
        results = self._execute_stats_query(site_id=site_id, 
            stats_range=stats_range,
            metrics='ga:pageviews,ga:visitors',
            sort='-ga:pageviews',
            dimensions = 'ga:country',
            filters=filters)
        formatted_results = self._format_results_grouped(results, 
            keys=['country', 'pageviews', 'visitors'], 
            grouping_key='country'
        )
        # Get rest of world results - no country dimension, exclude the named countries
        row_filters = 'ga:country!~%s' % countries_regex
        if extra_filters:
            row_filters = '%s;' % extra_filters
        row_results = self._execute_stats_query(site_id=site_id, 
            stats_range=stats_range,
            metrics='ga:pageviews,ga:visitors',
            sort='-ga:pageviews',
            filters=row_filters)
        formatted_row_results = self._format_results_flat(row_results, ['pageviews', 'visitors'])
        formatted_row_results[0]['country'] = 'ROW'
        formatted_results['ROW'] = formatted_row_results[0]
        return formatted_results

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

    def days_in_range(self):
        """
        The number of days in this StatsRange.
        """
        delta = self.end_date - self.start_date
        return delta.days + 1

    @classmethod
    def get_period(cls, date, frequency):
        if frequency == 'DAILY':
            return cls.get_one_day_period(date)
        if frequency == 'WEEKLY':
            return cls.get_one_week_period(date)
        if frequency == 'MONTHLY':
            return cls.get_one_month_period(date)

    @classmethod
    def get_previous_period(cls, current_period, frequency):
        if frequency == 'DAILY':
            previous_date = current_period.start_date - timedelta(days=1)
            return cls.get_one_day_period(previous_date)
        if frequency == 'WEEKLY':
            previous_date = current_period.end_date - timedelta(days=7)
            return cls.get_one_week_period(previous_date)
        if frequency == 'MONTHLY':
            previous_start = subtract_one_month(current_period.start_date)
            previous_end = current_period.start_date - timedelta(days=1)
            return cls("Previous Month", previous_start, previous_end)

    @classmethod
    def get_one_day_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One day", date, date)

    @classmethod
    def get_one_week_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One week", date-timedelta(days=6), date)

    @classmethod
    def get_one_month_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One month", subtract_one_month(date), date - timedelta(days=1))

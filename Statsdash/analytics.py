from googleapiclient import errors
import logging.config
import logging.handlers

import Statsdash.GA.config as config
from Statsdash.config import LOGGING
from Statsdash import utils


logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly', ]

with open(config.KEY_FILE, 'rb') as f:
    PRIVATE_KEY = f.read()


class Analytics:
    # MAKE MORE GENERIC/PLUGGABLE
    # TODO add docstring (copy from YouTube?)
    # NOTE should these classes inherit from a base class?

    config = NotImplemented


class GoogleAnalytics(Analytics):
    """
    Wrapper class for Google Analytics Management API.
    """

    def __init__(self, api):
        self.api = api

        # get report
        # TODO rename
        self.ga = self.api.data().ga()  # Returns the GA data Resource.

    def data_available(self, view_id, stats_date):
        """
        Determines whether the data is ready. The response contains a row for
        every hour. We only want the data once we have all 24 rows.

        Returns:
            * `bool` - Whether there are 24 rows of data in the response.
        """
        results = self._run_report(view_id, stats_date, stats_date,
                                   'ga:pageviews', dimensions='ga:dateHour')

        rows = results.get('rows')
        if not rows:
            logger.info(f'view_id {view_id} returned no rows for '
                        f'data_available check on {stats_date}')
            return False

        data_available = len(rows) == 24
        if not data_available:
            logger.info(f'view_id {view_id} data_available check on '
                        f'{stats_date} returned rows: {rows}')

        return data_available

    def rollup_ids(self, view_ids, start, end, metrics, aggregate_key=None, **kwargs):
        """
        Fetches analytics data for all the given GA views, reformats and
        aggregates the data and returns them as a single dict.

        Returns:
            * `list` of reformatted data for each GA view ID.
        """
        # TODO if these utils are only used in this class then they should be
        # private methods.
        output = []
        all_reports = self._fetch_multiple(view_ids, start, end, metrics, **kwargs)
        for report in all_reports:
            formatted_data = utils.format_data_rows(report)
            for row in formatted_data:
                # TODO we shouldn't use split all the time like this.
                utils.convert_to_floats(row, metrics.split(","))
            output.extend(formatted_data)
        return utils.aggregate_data(output, metrics.split(","), aggregate_key)

    def _fetch_multiple(self, view_ids, start, end, metrics, **kwargs):
        """
        Fetches the analytics data for multiple GA views. Excludes data with
        no rows. Logs empty rows.

        Args:
            * `view_ids` - `list` - A list of GA view ids.

        Returns:
            * `list` of results (`dict`).
        """
        all_reports = []
        for view_id in view_ids:
            results = self._run_report(view_id, start, end, metrics, **kwargs)
            if results.get('rows'):
                all_reports.append(results)
            else:
                self._log_no_data(view_id, start, end, metrics, **kwargs)
        return all_reports

    @staticmethod
    def _log_no_data(view_id, start, end, metrics, **kwargs):
        """
        Log that there was no data in the result. Include the dimensions and
        filters used in the query if applicable.
        """
        log_message = (f'No data for {view_id} on {start} - {end}.\n'
                       f'metrics: {metrics}')

        for kw in ['dimensions', 'filters']:
            s = 'None'
            val = kwargs.get(kw)
            if val:
                s = val.encode('utf-8')
            log_message += f'\n{kw}: {s}.'
            logger.debug(log_message)

    def _run_report(self, view_id, start, end, metrics, **kwargs):
        """
        Wraps `ga.get()`. Gets the Analytics data for a view (profile).

        Args:
            * `view_id` - `str` - View ID for retrieving Analytics data.
            * `start_date` - `str` - Start date for fetching Analytics data.
            * `end_date` - `str` - End date for fetching Analytics data.
            * `metrics` - `str` - A comma-separated list of Analytics metrics.
            * `kwargs` - max_results, filters, dimensions, include_empty_rows,
              sort, samplingLevel, segment, start_index, output.

        Returns:
            * `dict`
        """
        # NOTE we're running this multiple times per site.
        kwargs['include_empty_rows'] = True  # always True
        query = self.ga.get(view_id, start, end, metrics, **kwargs)
        return self._execute_query(query)

    def _execute_query(self, query):
        """
        Wrapper to run `query.execute()` method. Calls the query object's
        execute method to send the query to Google Analytics servers.

        Args:
            * `query` - `str` - Unique table ID for retrieving Analytics
            data.

        Returns:
            * `dict`

        Raises:
            * `HttpError` if http error occurs.
            * `Exception` if any other error occurs during the execution.
        """
        # TODO we might need a wait for it type wrapper method.
        # https://stackoverflow.com/questions/41713234/better-way-to-write-a-polling-function-in-python
        try:
            return query.execute()
        except errors.HttpError as e:
            logger.warning(
                f'HTTP error {e.resp.status} occurred:\n{e.content}'
            )
        except Exception as e:
            logger.warning(
                f'Unknown error from GA\nType: {str(type(e))} {str(e)}'
            )


class YouTubeAnalytics(Analytics):
    pass

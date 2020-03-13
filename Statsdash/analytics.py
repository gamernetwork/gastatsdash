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


# TODO split this into separate classes
class YouTubeAnalytics(Analytics):
    """
    Wrapper class for YouTube analytics APIs.
    """
    youtube = None
    youtube_analytics = None

    def __init__(self):
        """
        Initialise credentials and build api object to query.
        """
        credentials = service_account.Credentials.from_service_account_file(
            config.KEY_FILE,
            scopes=SCOPES
        )

        self.youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            credentials=credentials,
        )
        self.youtube_analytics = discovery.build(
            YOUTUBE_ANALYTICS_API_SERVICE_NAME,
            YOUTUBE_ANALYTICS_API_VERSION,
            credentials=credentials,
        )
        self.report_resource = self.youtube_analytics.reports()

    def execute_query(self, query):
        """
        Try to execute the API query.
        """
        try:
            results = query.execute()
            return results
        except errors.HttpError as e:
            logger.warning(
                "HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
            )

    def data_available(self, view_id, stats_date):
        # NOTE make metrics constant?
        results = self._run_report(view_id, stats_date, stats_date,
                                   'views', dimensions='ga:dateHour')
        return bool(results.get('rows'))

    def _run_report(self, channel_id, start_date, end_date, metrics, **kwargs):
        analytics_query_response = self.youtube_analytics.reports().query(
            ids='contentowner==%s' % config.content_owner_id,
            startdate=start_date,
            enddate=end_date,
            metrics=metrics,
            filters='channel==%s' % channel_id,
            **kwargs,
        )
        return self.execute_query(analytics_query_response)

    # TODO make private (only used by roll up stats)
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
            results = self._run_report(
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

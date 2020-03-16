from googleapiclient import errors
import logging.config
import logging.handlers

from Statsdash.config import LOGGING
from Statsdash.utils import utils

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')


class Analytics:
    """
    Base class for wrapper classes around google-api-python-client data
    resources.

    See https://github.com/googleapis/google-api-python-client/blob/master/docs/dyn/index.md
    """

    identifier = NotImplemented  # Used for logs, e.g. 'Google Analytics'.

    def __init__(self, data_resource):
        self.data_resource = data_resource  # the API resource to wrap.

    def get_data(self, ids, start, end, metrics, aggregate_key=None, **kwargs):
        """
        Fetches analytics data for all the given IDs, reformats and
        aggregates the data and returns them as a single dict.

        Returns:
            * `list` of reformatted data for each ID.
        """
        output = []
        all_reports = self._fetch_multiple(ids, start, end, metrics, **kwargs)
        for report in all_reports:
            formatted_data = utils.format_data_rows(report)
            for row in formatted_data:
                # TODO we shouldn't use split all the time like this.
                utils.convert_to_floats(row, metrics.split(","))
            output.extend(formatted_data)
        return utils.aggregate_data(output, metrics.split(","), aggregate_key)

    def _fetch_multiple(self, ids, start, end, metrics, **kwargs):
        """
        Fetches the analytics data for multiple ids. Excludes data with
        no rows. Logs empty rows.

        Args:
            * `ids` - `list` - A list of ids.

        Returns:
            * `list` of results (`dict`).
        """
        all_reports = []
        for _id in ids:
            # TODO replace with _id with ids
            results = self._run_report(_id, start, end, metrics, **kwargs)
            if results:
                all_reports.append(results)
            else:
                self._log_no_data(_id, start, end, metrics, **kwargs)
        return all_reports

    def _execute_query(self, query):
        """
        Wrapper to run `query.execute()` method. Calls the query object's
        execute method to send the query to API servers.

        Args:
            * `query` - `str` - The query object to be executed.

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
                f'Unknown error from {self.identifier}\nType: {str(type(e))} '
                f'{str(e)}'
            )

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

    def _run_report(self, _id, start, end, metrics, **kwargs):
        raise NotImplementedError(
            'Subclasses of Analytics need to implement a run report method.'
        )


class GoogleAnalytics(Analytics):
    """
    Wrapper class for Google Analytics Management API.
    """
    identifier = 'Google Analytics'

    class Metrics:
        pageviews = 'ga:pageviews'

    class Dimensions:
        date_hour = 'ga:dateHour'

    def data_available(self, _id, stats_date):
        """
        Determines whether the data is ready. The response contains a row for
        every hour. We only want the data once we have all 24 rows.

        Returns:
            * `bool` - Whether there are 24 rows of data in the response.
        """
        results = self._run_report(
            _id,
            stats_date,
            stats_date,
            self.Metrics.pageviews,
            dimensions=self.Dimensions.date_hour
        )
        rows = results.get('rows')
        if not rows:
            logger.info(f'ID {_id} returned no rows for '
                        f'data_available check on {stats_date}')
            return False

        data_available = len(rows) == 24
        if not data_available:
            logger.info(f'ID {_id} data_available check on '
                        f'{stats_date} returned rows: {rows}')
        return data_available

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
        query = self.data_resource.get(
            ids=view_id,
            start_date=start,
            end_date=end,
            metrics=metrics,
            **kwargs
        )
        return self._execute_query(query)


class YouTubeAnalytics(Analytics):
    """
    Wrapper class for YouTube analytics APIs.
    """
    identifier = 'YouTube Analytics'

    class Metrics:
        pageviews = 'views'

    def __init__(self, data_resource, content_owner_id):
        super().__init__(data_resource)
        self.content_owner_id = content_owner_id

    def data_available(self, _id, stats_date):
        filters = f'channel=={_id}'
        results = self._run_report(_id, stats_date, stats_date,
                                   self.Metrics.pageviews, filters=filters)
        # TODO duplication
        rows = results.get('rows')
        if not bool(rows):
            logger.info(f'ID {_id} returned no rows for '
                        f'data_available check on {stats_date}')
            return False
        return True

    def _run_report(self, _id, start_date, end_date, metrics, **kwargs):
        filters = self._prepare_filters(_id, kwargs.pop('filters', None))
        query = self.data_resource.query(
            ids=f'contentowner=={self.content_owner_id}',
            startDate=start_date,
            endDate=end_date,
            metrics=metrics,
            filters=filters,
            **kwargs,
        )
        return self._execute_query(query)

    def _prepare_filters(self, _id, filters):
        """
        Add the channel ID to the filters arg. The YouTube Analytics API takes
        the channel IDs in the filter argument. If there are already specified
        filters, append the ID to the filters.
        """
        # TODO test
        if filters:
            return filters + ';channel==%s' % _id
        return 'channel==%s' % _id


class YouTubeChannels(Analytics):
    """
    Wrapper class for YouTube Data API Channels resource.
    """
    def get_data(self, ids, **kwargs):
        id_combo = ','.join(ids)
        results = self._run_report(id_combo)
        stats = {}
        for row in results:  # TODO k, v refactor?
            metrics = row['statistics'].keys()
            data = row['statistics']
            data = utils.convert_to_floats(metrics, data)
            for metric in data:
                if metric in data:
                    stats[metric] += data[metric]
                else:
                    stats[metric] = data[metric]
        return stats

    def _run_report(self, _id, **kwargs):
        query = self.data_resource.list(
            id=_id,
            part='statistics',
            **kwargs,
        )
        return self._execute_query(query)

    #
    # def get_video(self, id):
    #     """
    #     Returns info on video with specified id.
    #     """
    #     video_results = self.youtube.videos().list(
    #         id=id,
    #         part="snippet"
    #     )
    #     return self._execute_query(video_results)

from googleapiclient import errors
import logging.config
import logging.handlers

from Statsdash import utils
from Statsdash.config import LOGGING

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
                utils.convert_to_floats(row, metrics)
            output.extend(formatted_data)
        return utils.aggregate_data(output, metrics, aggregate_key)

    def _fetch_multiple(self, ids, start, end, metrics, **kwargs):
        """
        Fetches the analytics data for multiple ids. Excludes data with
        no rows. Logs empty rows.

        Args:
            * `ids` - `list` - A list of ids. For GA, ids.
            * `start` - `str` - Start date of reports, e.g. `'2020-03-18'`.
            * `end` - `str` - End date of reports, e.g. `'2020-03-19'`.
            * `metrics` - `list` - metric identifiers, e.g, `['views' ,'users']`.

        Returns:
            * `list` of results (`dict`).
        """
        all_reports = []
        for _id in ids:
            results = self._run_report(_id, start, end, metrics, **kwargs)
            if results and results.get('rows'):
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
        # NOTE original implementation used a wait for it mechanism.
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
        metrics = ','.join(metrics)
        dimensions =  kwargs.get('dimensions')
        if dimensions:
            kwargs['dimensions'] = ','.join(dimensions)
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
        """
        Constants for metric identifiers. First value is metric identifier as
        Google expects it. Second value is our identifier for the metric.
        """
        pageviews = ('ga:pageviews', 'pageviews')
        users = ('ga:users', 'users')
        sessions = ('ga:sessions', 'sessions')
        pv_per_sessions = ('ga:pageviewsPerSession', 'pv_per_session')
        avg_session_time = ('ga:avgSessionDuration', 'avg_session_time')

    class Dimensions:
        """
        Constants for dimension identifiers. First value is dimension
        identifier as Google expects it. Second value is our identifier for the
        dimension.
        """
        country = ('ga:country', 'country')
        date_hour = ('ga:dateHour', 'date_hour')
        device_category = ('ga:deviceCategory', 'device_category')
        host = ('ga:hostname', 'host')
        social_network = ('ga:socialNetwork', 'social_network')
        source = ('ga:sourceMedium', 'source_medium')
        path = ('ga:pagePath', 'path')
        title = ('ga:pageTitle', 'title')

    class Countries:
        czech_republic = 'Czec'
        germany = 'Germa'
        denmark = 'Denma'
        spain = 'Spai'
        france = 'Franc'
        italy = 'Italy'
        portugal = 'Portug'
        sweden = 'Swede'
        poland = 'Polan'
        brazil = 'Brazi'
        belgium = 'Belgiu'
        netherlands = 'Netherl'
        united_kingdom = 'United Ki'
        ireland = 'Irela'
        united_states = 'United St'
        canada = 'Canad'
        australia = 'Austral'
        new_zealand = 'New Ze'

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
            [self.Metrics.pageviews[0]],
            dimensions=[self.Dimensions.date_hour[0]],
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
            * `view_id` - `str` - view ID for retrieving analytics data.
            * `start_date` - `str` - start date for fetching analytics data.
            * `end_date` - `str` - end date for fetching analytics data.
            * `metrics` - `list` - analytics metrics.
            * `kwargs` - max_results, filters, dimensions, include_empty_rows,
              sort, samplingLevel, segment, start_index, output.

        Returns:
            * `dict`
        """
        metrics = ','.join(metrics)
        kwargs['dimensions'] = self._get_dimensions(kwargs['dimensions'])
        kwargs['include_empty_rows'] = True  # always True
        if type(view_id) == dict:
            view_id = list(view_id.values())[0]
        print(view_id)
        query = self.data_resource.get(
            ids=view_id,
            start_date=start,
            end_date=end,
            metrics=metrics,
            **kwargs
        )
        return self._execute_query(query)

    @staticmethod
    def _get_dimensions(dimensions):
        if dimensions:
            return ','.join(dimensions)
        return None


class YouTubeAnalytics(Analytics):
    """
    Wrapper class for YouTube analytics reports API.
    """
    identifier = 'YouTube Analytics'

    class Metrics:
        views = ('views', 'views')
        estimated_minutes_watched = ('estimatedMinutesWatched', 'estimated_minutes_watched')
        subscribers_gained = ('subscribersGained', 'subscribers_gained')
        subscribers_lost = ('subscribersLost', 'subscribers_lost')
        likes = ('likes', 'likes')
        dislikes = ('dislikes', 'dislikes')
        comments = ('comments', 'comments')
        shares = ('shares', 'shares')

    class Dimensions:
        channel = ('channel', 'channel')
        country = ('country', 'country')
        insight_traffic_source_type = ('insightTrafficSourceType', 'insight_traffic_source_type')
        video = ('video', 'video')

    def __init__(self, data_resource, content_owner_id):
        super().__init__(data_resource)
        self.content_owner_id = content_owner_id

    def data_available(self, _id, stats_date):
        """
        Determines whether the data is ready. If there are any rows, the data
        is ready.

        Returns:
            * `bool` - Whether there are rows in the response.
        """
        filters = f'channel=={_id}'
        metrics = [self.Metrics.views[0]]
        results = self._run_report(_id, stats_date, stats_date, metrics, filters=filters)
        rows = results.get('rows')
        if not bool(rows):
            logger.info(f'ID {_id} returned no rows for '
                        f'data_available check on {stats_date}')
            return False
        return True

    def _run_report(self, channel_id, start, end, metrics, **kwargs):
        """
        Wraps `reports.query()`. Gets the analytics data for a channel.

        Args:
            * `channel_id` - `str` - View ID for retrieving Analytics data.
            * `start` - `str` - Start date for report.
            * `end` - `str` - End date for report.
            * `metrics` - `list` - Analytics metrics.
            * `kwargs` - max_results, filters, dimensions, include_empty_rows,
              sort, samplingLevel, segment, start_index, output.

        Returns:
            * `dict`
        """
        metrics = ','.join(metrics)
        filters = self._prepare_filters(channel_id, kwargs.pop('filters', None))
        query = self.data_resource.query(
            ids=f'contentOwner=={self.content_owner_id}',
            startDate=start,
            endDate=end,
            metrics=metrics,
            filters=filters,
            **kwargs,
        )
        return self._execute_query(query)

    @staticmethod
    def _prepare_filters(_id, filters):
        """
        Add the channel ID to the filters arg. The YouTube Analytics API takes
        the channel IDs in the filter argument. If there are already specified
        filters, append the ID to the filters.
        """
        if filters:
            return filters + ';channel==%s' % _id
        return 'channel==%s' % _id


class YouTubeVideos(Analytics):
    """
    Wrapper class for YouTube Data API Channels resource.
    """
    def _run_report(self, _id, **kwargs):
        raise NotImplementedError()

    def get_video(self, id):
        """
        Returns info on video with specified id.
        """
        video_results = self.data_resource.list(
            id=id,
            part='snippet'
        )
        return self._execute_query(video_results)


def third_party_metrics(metrics):
    """
    Gets the Google/YouTube identifier for an iterable of metrics.

    Args:
        * `metrics` - `list` - a list of metrics

    Returns:
        `list`
    """
    return [m[0] for m in metrics]


def our_metrics(metrics):
    """
    Gets the our identifier for an iterable of metrics.

    Args:
        * `metrics` - `list` - a list of metrics

    Returns:
        `list`
    """
    return [m[1] for m in metrics]

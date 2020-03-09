from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import errors
from httplib2 import Http
import json
import logging
import logging.config
import logging.handlers
import random
import time

# TODO fix imports
import Statsdash.GA.config as config
from Statsdash.config import LOGGING
import Statsdash.utilities as utils

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly', ]

with open(config.KEY_FILE, 'rb') as f:
    PRIVATE_KEY = f.read()


class Analytics(object):
    # TODO add docstring (copy from YouTube?)
    # NOTE should these classes inherit from a base class?

    def __init__(self):
        credentials = InstalledAppFlow.from_client_secrets_file(
            config.KEY_FILE,
            scopes=SCOPES
        )
        http_auth = credentials.authorize(Http())
        ga_service = build('analytics', 'v3', http=http_auth)
        self.ga = ga_service.data().ga()

    def execute_query(self, query):
        for i in range(1, 6):
            try:
                return query.execute()
            except errors.HttpError as e:
                error = json.loads(e.content)
                if i == 5:
                    logger.warning("Error, request has failed 5 times")
                    raise
                if error['error'].get('code') == 500:
                    logger.warning("500 Error, #%d, trying again...", i)
                    # NOTE Why random?
                    time.sleep((2 ** i) + random.random())
                    continue
                # TODO merge ifs
                if error['error'].get('code') == 503:
                    logger.warning("503 Error, #%d, trying again...", i)
                    time.sleep((2 ** i) + random.random())
                    continue
                else:
                    raise
            except Exception as e:
                logger.warning("Unknown error from GA")
                logger.warning(f'Type: {str(type(e))} {str(e)}')
        return None

    def data_available(self, site_id, stats_date):
        # TODO: Persist these results in a cache so we don't smash our rate
        # limit

        query = self.ga.get(
            ids=site_id,
            start_date=stats_date,
            end_date=stats_date,
            metrics="ga:pageviews",
            dimensions="ga:dateHour",
            include_empty_rows=True,
        )
        results = query.execute()

        # NOTE why 24?
        try:
            data_available = len(results['rows']) == 24
            # TODO don't use try except.
        except KeyError:
            logger.info("site_id %s returned no rows for data_available check on %s" % (site_id, stats_date))
            return False
        if not data_available:
            logger.info("site_id %s data_available check on %s returned rows: %s" % (site_id, stats_date, results['rows']))
        return data_available

    def run_report(self, site_id, start, end, metrics=None, dimensions=None,
                   filters=None, sort=None, max_results=None):
        # NOTE could using kwargs be valuable here?
        query = self.ga.get(
            ids=site_id,
            start_date=start,
            end_date=end,
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            sort=sort,
            max_results=max_results,
            include_empty_rows=True,
        )
        return self.execute_query(query)

    # TODO de-dupe from other class.
    def rollup_ids(self, properties, start, end, metrics,
                   dimensions=None, filters=None, sort=None, max_results=None,
                   aggregate_key=None):
        main_row = []
        for property_details in properties:
            id = property_details['id']
            # TODO use kwargs
            results = self.run_report(
                id,
                start,
                end,
                metrics=metrics,
                dimensions=dimensions,
                filters=filters,
                sort=sort,
                max_results=max_results,
            )
            rows = utils.format_data_rows(results)
            if rows:
                for row in rows:
                    row = utils.convert_to_floats(row, metrics.split(","))
                main_row.extend(rows)
            else:
                logger.debug(f'No data for {id} on {start} - {end}')
                # NOTE why is this happening here.
                str_dimensions = "None"
                if dimensions:
                    str_dimensions = dimensions.encode('utf-8')
                str_filters = "None"
                if filters:
                    str_filters = filters.encode('utf-8')
                logger.debug(
                    f'For metrics: {metrics}  dimensions: {str_dimensions} '
                    f'filters: {str_filters}'
                )
        main_row = utils.aggregate_data(main_row, metrics.split(","), aggregate_key)
        return main_row

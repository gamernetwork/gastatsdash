from pprint import pprint

from Statsdash.analytics import third_party_metrics, our_metrics
from Statsdash.config import LOGGING
from Statsdash.stats_range import StatsRange
from Statsdash.utils import utils


class AggregateData:

    analytics = None
    metrics = []
    extra_metrics = []
    dimensions = []
    aggregate_key = None
    filters = None
    match_key = None
    sort_by = None
    sort_rows_by = None
    limit = None
    extra_params = {}

    def __init__(self, sites, period, frequency):
        self.sites = sites
        self.frequency = frequency
        # TODO pass name into get_pervious_period
        previous_period = StatsRange.get_previous_period(period, self.frequency)  # remove literal
        previous_period.name = 'previous'
        yearly_period = StatsRange.get_previous_period(period, "YEARLY")
        yearly_period.name = 'yearly'
        self.periods = [period, previous_period, yearly_period]

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
        current_period = data[0]
        other_periods = data[1:]
        new_data = []
        #iterate over every item in the current period and get the change versus prevous periods
        # NOTE this will cause a bug if the other period doesn't have the data for all the same rows. Should be the exact same rows.

        for i, current_period_data in enumerate(current_period):
            joined_data = current_period_data
            for j, other_period in enumerate(other_periods, 1):
                period = self.periods[j]
                try:
                    other_period_data = other_period[i]
                    change = utils.get_change(
                        current_period_data,
                        other_period_data,
                        our_metrics(self.metrics) + self.extra_metrics,
                        match_key=self.match_key
                    )
                    change = utils.prefix_keys(change, period.name + '_')
                    joined_data.update(change)
                # TODO test
                except IndexError:
                    pass
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
            data = self.analytics.get_data(
                self.site_ids[site],
                period.get_start(),
                period.get_end(),
                # TODO rename method.
                metrics=','.join(third_party_metrics(self.metrics)),
                dimensions=','.join(third_party_metrics(self.dimensions)),
                filters=self.filters,
                sort=self.sort_by,
                aggregate_key=self.aggregate_key,
                **self.extra_params,
            )
            data = self._get_extra_data(period, site, data)

            # data is a list with a dict for each id in site config
            if data:
                data = self._format_all_data(data, site)
                all_sites_data = all_sites_data + data
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

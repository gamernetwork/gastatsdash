from datetime import date, datetime, timedelta
import logging.config, logging.handlers

from Statsdash import config
from Statsdash.aggregate_data import google, youtube
from Statsdash.render import get_environment
from Statsdash.resources import get_google_analytics, get_youtube_analytics
from Statsdash.stats_range import StatsRange
from Statsdash.utils import camel_to_lowercase_words, date, Frequency

logging.config.dictConfig(config.LOGGING)
logger = logging.getLogger('report')


class Report:
    """
    Gathers data from analytics and renders it as html.
    """
    data = []
    img_data = None
    env = get_environment()
    template = 'GA/base.html'

    def __init__(self, sites, period, frequency, subject):
        self.resource = self.get_resource()
        self.sites = sites
        self.period = period
        self.frequency = frequency
        self.subject = subject
        self.warning_sites = []

        # NOTE maybe nicer way to handle this
        self.today = self.period.end_date
        self.first = datetime(self.today.year, self.today.month, 1).date()
        self.last = date.add_one_month(self.first) - timedelta(days=1)
        self.num_days = (self.last - self.period.end_date).days

        # TODO make dynamic
        logger.debug(f'Running {self.label}.')

    @property
    def label(self):
        """
        Label for the report class in debug log. By default the class name is
        used.

        Returns:
            * `str`
        """
        return camel_to_lowercase_words(self.__class__.__name__)

    @property
    def frequency_label(self):
        """
        Label for the period of change, e.g. where frequency == 'monthly',
        label == 'MoM'.

        Returns:
            * `str`
        """
        first_letter = self.frequency[0].upper()
        label = first_letter + "o" + first_letter
        return label

    def get_template(self):
        return self.env.get_template(self.template)

    def get_subject(self):
        """
        Return the subject of the email that includes the dates for this period
        """
        if self.frequency in [Frequency.DAILY, Frequency.WOW_DAILY]:
            subject = ' '.join([self.subject, self.period.end_date.strftime('%a %d %b %Y')])
        elif self.frequency == Frequency.WEEKLY:
            weekly_date = self.period.start_date.strftime('%a %d %b %Y') + ' - ' + self.period.end_date.strftime('%a %d %b %Y')
            subject = ' '.join([self.subject, weekly_date])
        else:
            subject = ' '.join([self.subject, self.period.start_date.strftime('%B %Y')])
        return subject

    def generate_html(self):
        """
        Get formatted data and render to template
        """
        tables = self._get_tables()

        html = self.get_template().render(
            **self._get_render_context(),
            **tables
        )
        return html

    def get_resource(self):
        raise NotImplementedError()

    def _get_render_context(self):
        return {
            'subject': self.get_subject(),
            'change': self.frequency_label,
            'report_span': self.frequency,
            'warning_sites': self.warning_sites,
            'num_days': self.num_days,
        }

    # TODO test and docstring
    def _get_tables(self):
        args = [self.resource, self.sites, self.period, self.frequency]
        return {d.table_label: d(*args).get_table() for d in self.data}

    def check_data_availability(self):
        raise NotImplementedError()


class YouTubeReport(Report):

    data = [
        youtube.ChannelSummaryData,
        youtube.ChannelStatsData,
        youtube.CountryData,
        youtube.VideoData,
        youtube.TrafficSourceData,
    ]
    template = 'Youtube/base.html'

    @property
    def label(self):
        return 'youtube report'

    def get_resource(self):
        return get_youtube_analytics()

    def check_data_availability(self):
        args = [self.resource, self.sites, self.period, self.frequency]
        youtube.ChannelStatsData(*args)


# TODO break this into a daily report and a montly report
class AnalyticsCoreReport(Report):
    """
    Google Analytics data report for a given collection of sites. Converts the
    report into HTML.
    """
    data = [
        google.SummaryData,
        google.SiteSummaryData,
        google.CountryData,
        google.ArticleData,
        google.TrafficSourceData,
        google.DeviceData,
    ]
    template = 'GA/base.html'

    def __init__(self, sites, period, frequency, subject):
        super().__init__(sites, period, frequency, subject)
        if self.sites == config.GOOGLE['ALL_NETWORK_SITES']:
            self.all_sites = True
        else:
            self.all_sites = False

    def check_data_availability(self):
        args = [self.resource, self.sites, self.period, self.frequency]
        google.SummaryData(*args)

    def get_resource(self):
        return get_google_analytics()

    def _get_render_context(self):
        context = super()._get_render_context()
        context['site'] = self.get_site()
        context['all_sites'] = self.all_sites
        return context

    # TODO sort this
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        elif self.all_sites:
            return config.GOOGLE['ALL_SITES_NAME']

    def _get_tables(self):
        tables = super()._get_tables()
        tables['summary_table'] = tables['summary_table'][0]
        tables['network_summary_table'] = self._get_network_summary_table()[0]
        if self.frequency != Frequency.MONTHLY:
            tables['network_month_summary_table'] = self._get_network_month_summary_table()[0]
            tables['full_month_summary_table'] = self._get_full_month_summary_table()[0]
            tables['month_summary_table'] = self._get_month_summary_table()[0]
        return tables

    def _get_network_summary_table(self):
        network_data = google.SummaryData(self.resource, config.GOOGLE['TABLES'].keys(), self.period, self.frequency)
        return network_data.get_table()

    def _get_month_summary_table(self):
        if self.frequency != Frequency.MONTHLY:
            month_range = StatsRange('Month to date Aggregate', self.first, self.today)
            month_summary_data = google.SummaryData(self.resource, self.sites, month_range, self.frequency)
            return month_summary_data.get_table()
        return None

    def _get_full_month_summary_table(self):
        # TODO clean, test, mock
        month_range = self._get_month_range()
        full_month_data = google.SummaryData(self.resource, self.sites, month_range, self.frequency)
        return full_month_data.get_table()

    def _get_network_month_summary_table(self):
        month_range = self._get_month_range()
        if not self.all_sites:
            network_month_data = google.SummaryData(self.resource, config.GOOGLE['TABLES'], month_range, self.frequency)
            return network_month_data.get_table()
        return None

    def _get_month_range(self):
        return StatsRange('Month to date Aggregate', self.first, self.last)

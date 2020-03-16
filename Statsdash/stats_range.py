from datetime import timedelta
from dateutil.relativedelta import relativedelta


class StatsRange:

    class Frequency:
        DAILY = 'DAILY'
        WOW_DAILY = 'WOW_DAILY'
        WEEKLY = 'WEEKLY'
        MONTHLY = 'MONTHLY'
        YEARLY = 'YEARLY'

    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def get_start(self):
        return self._get_formatted_date(self.start_date)

    def get_end(self):
        return self._get_formatted_date(self.end_date)

    def days_in_range(self):
        """
        The number of days in this StatsRange.

        Returns:
            `int`
        """
        delta = self.end_date - self.start_date
        return delta.days + 1

    # TODO come back to these two methods and sense check them.

    @classmethod
    def get_period(cls, date, frequency):

        if frequency in [cls.Frequency.DAILY, cls.Frequency.WOW_DAILY]:
            return cls.get_one_day_period(date)
        if frequency == cls.Frequency.WEEKLY:
            return cls.get_one_week_period(date)
        if frequency == cls.Frequency.MONTHLY:
            return cls.get_one_month_period(date)

    @classmethod
    def get_previous_period(cls, current_period, frequency):

        if frequency not in cls.Frequency.__dict__:
            raise ValueError('frequency value not valid')

        if frequency == cls.Frequency.DAILY:
            previous_date = current_period.start_date - timedelta(days=1)
            return cls.get_one_day_period(previous_date)
        if frequency == cls.Frequency.WOW_DAILY:
            previous_date = current_period.start_date - timedelta(days=7)
            return cls.get_one_day_period(previous_date)
        if frequency == cls.Frequency.WEEKLY:
            # NOTE behaviour of this method is strange.
            previous_date = current_period.end_date - timedelta(days=7)
            return cls.get_one_week_period(previous_date)
        if frequency == cls.Frequency.MONTHLY:
            previous_start = current_period.start_date - relativedelta(months=1)
            previous_end = current_period.start_date - timedelta(days=1)
            return cls("Previous Month", previous_start, previous_end)
        if frequency == cls.Frequency.YEARLY:
            previous_start = current_period.start_date - relativedelta(years=1)
            previous_end = current_period.end_date - relativedelta(years=1)
            return cls("Period Last Year", previous_start, previous_end)

    @classmethod
    def get_one_day_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One day", date, date)

    @classmethod
    def get_one_week_period(cls, date):
        """
        Return instantiated one week period for date.
        """
        date = date - timedelta(days=1)
        return cls("One week", date - timedelta(days=6), date)

    @classmethod
    def get_one_month_period(cls, date):
        """
        Return instantiated one month period for date.
        """
        start_date = date - relativedelta(months=1)
        return cls("One month", start_date, date - timedelta(days=1))

    @staticmethod
    def _get_formatted_date(d):
        return d.isoformat()

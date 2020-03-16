from datetime import datetime, date, timedelta
import calendar


def get_month_day_range(date):
    """
    For a date, returns the start and end date of the month specified
    """
    first_day = date.replace(day=1)
    last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day


def add_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month earlier.

    Note that the resultant day of the month might change if the following
    month has fewer days:

        >>> add_one_month(datetime.date(2010, 1, 31))
        datetime.date(2010, 2, 28)
    """

    one_day = timedelta(days=1)
    one_month_later = t + one_day

    while one_month_later.month == t.month:  # advance to start of next month
        one_month_later += one_day

    target_month = one_month_later.month

    # issue with this conditional when t.day = 28 (i.e. feb, never gets to the end of next month)
    # while one_month_later.day < 31  ? nope doesnt work if not trying to get the laast of the month

    while one_month_later.day < t.day:  # advance to appropriate day, needs to always get to the end of the month
        one_month_later += one_day
        if one_month_later.month != target_month:  # gone too far
            one_month_later -= one_day
            break

    return one_month_later


WEEKDAY_INDEXES = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
    'Saturday': 5,
    'Sunday': 6,
}


def find_last_weekday(start_date, weekday):
    """
    given a starting date and a string weekday, return the date object for the
    closest date in the past with that weekday.  returns today if that matches.

    eg: last_weekday(date(01,01,2015), "Monday")
    returns date(29,12,2014) since this is the previous monday
    """
    desired_weekday = WEEKDAY_INDEXES[weekday]
    current_weekday = start_date.weekday()
    if desired_weekday == current_weekday:
        days = 0
    if desired_weekday < current_weekday:
        days = current_weekday - desired_weekday
    if desired_weekday > current_weekday:
        days = 7 - (desired_weekday - current_weekday)
    return start_date - timedelta(days=days)


def find_next_weekday(start_date, weekday, force_future=False):
    """
    Given a starting date and a string weekday, return the date object for the
    closest date in the future with that weekday.  returns today if that matches.

    Args:
        `start_date` - datetime object - datetime to anchor from
        `weekday` - string - one of "Monday"-"Sunday"
        `[force_future]` - boolean - return the weekday from the following week
            if `start_date` matches our desired weekday.  Defaults to False

    eg: next_weekday(date(01,01,2015), "Monday")
    returns date(05,01,2015) since this is the next monday
    """
    desired_weekday = WEEKDAY_INDEXES[weekday]
    current_weekday = start_date.weekday()
    if desired_weekday == current_weekday:
        days = 0
        if force_future:
            days = 7
    if desired_weekday < current_weekday:
        days = 7 - current_weekday + desired_weekday
    if desired_weekday > current_weekday:
        days = desired_weekday - current_weekday
    return start_date + timedelta(days=days)


def list_of_months(today, num_years):
    """
    Return a list of monthly stats ranges for the amount of years specified
    """
    # find last day of month??????
    # today = self.period.end_date
    start_month = date(today.year - num_years, today.month, 1)
    end_month = today + timedelta(
        days=1)  # first of next month so includes this month
    current = start_month
    month_stats_range = []
    while (current.year, current.month) != (end_month.year, end_month.month):
        start_date = current
        end_date = get_month_day_range(current)[1]
        name = start_date.strftime("%b-%Y")
        month_stats_range.append(StatsRange(name, start_date, end_date))
        current = add_one_month(start_date)

    return month_stats_range

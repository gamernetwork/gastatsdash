import datetime

def add_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month earlier.
    
    Note that the resultant day of the month might change if the following
    month has fewer days:
    
        >>> add_one_month(datetime.date(2010, 1, 31))
        datetime.date(2010, 2, 28)
    """
    one_day = datetime.timedelta(days=1)
    one_month_later = t + one_day
    while one_month_later.month == t.month:  # advance to start of next month
        one_month_later += one_day
    target_month = one_month_later.month
    while one_month_later.day < t.day:  # advance to appropriate day
        one_month_later += one_day
        if one_month_later.month != target_month:  # gone too far
            one_month_later -= one_day
            break
    return one_month_later

def subtract_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month later.
    
    Note that the resultant day of the month might change if the following
    month has fewer days:
    
        >>> subtract_one_month(datetime.date(2010, 3, 31))
        datetime.date(2010, 2, 28)
    """
    one_day = datetime.timedelta(days=1)
    one_month_earlier = t - one_day
    while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
        one_month_earlier -= one_day
    return one_month_earlier

WEEKDAY_INDEXES = {
    'Monday':       0,
    'Tuesday':      1, 
    'Wednesday':    2,
    'Thursday':     3,
    'Friday':       4,
    'Saturday':     5, 
    'Sunday':       6,
}

def find_last_weekday(start_date, weekday):
    """
    Given a starting date and a string weekday, return the date object for the 
    closest date in the past with that weekday.  Returns today if that matches.

    EG: last_weekday(Date(01,01,2015), "Monday")
    returns Date(29,12,2014) since this is the previous Monday
    """
    desired_weekday = WEEKDAY_INDEXES[weekday]
    current_weekday = start_date.weekday()
    if desired_weekday == current_weekday:
        days = 0
    if desired_weekday < current_weekday:
        days = current_weekday - desired_weekday
    if desired_weekday > current_weekday:
        days = 7 - (desired_weekday - current_weekday)
    return start_date - datetime.timedelta(days=days)

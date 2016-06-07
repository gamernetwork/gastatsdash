from datetime import datetime, timedelta

def format_data_rows(results):
	"""
	Returns results from analytics as a list of dictionaries with correct key/value pairs of data 
	"""
	rows = []
	for row in results.get("rows", []):
		data = {}
		for count, column in enumerate(results.get("columnHeaders", [])):
			data[column['name']] = row[count]
		rows.append(data)
	return rows
	
	
def sig_fig(sf, num):
	condensed_num = "%0.*g" % ((sf), num)
	return float(condensed_num)
	
	
def percentage(change, total):
	try:
		percentage = (change / float(total)) * 100
	except ZeroDivisionError:
		percentage = 0		
	return percentage
	
	
def rate_per_1000(metric, comparative):
	try: 
		rate = metric / float(comparative/1000.0)
	except ZeroDivisionError:
		rate = 0
	return rate

def sort_data(unsorted_list, metric, limit = 100, reverse=True):           
    """
    Sorts a list of dictionaries by the "metric" key given
    """
    sorted_list = sorted(unsorted_list, key = lambda k: k[metric], reverse = reverse)
    top_results = sorted_list[:limit]      
    return top_results  

def list_search(to_search, key, value):
    """
    Given a list of dictionaries, returns the dictionary that matches the given key value pair
    """
    result = [element for element in to_search if element[key] == value]
    if result:
        return result[0]
    else:
        raise KeyError

def aggregate_data(table, match_key, aggregate_keys):
    """
    
    """
    new_table = []
    for row in table:
        try: 
            result = list_search(new_table, match_key, row[match_key])
            for key in aggregate_keys:
                result[key] += row[key]
        except KeyError:
            new_table.append(row)
    return new_table


def add_change(this_period, previous_period, match_key, change_keys):
    
    for row in this_period:
        try:
            result = list_search(previous_period, match_key, row[match_key])
            for key in change_keys:
                row['change_%s' % key]  = row[key] - result[key]
                row['percentage_%s' % key] = percentage(row['change_%s' % key], result[key])
        except KeyError:
            for key in change_keys:
                row['change_%s' % key]  = 0
                row['percentage_%s' % key] = 0
    return this_period






    
	
class StatsRange(object):
   
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def _get_formatted_date(self, d):
        return d.isoformat()

    def get_start(self):
        return self._get_formatted_date(self.start_date)

    def get_end(self):
        return self._get_formatted_date(self.end_date)
         

    def days_in_range(self):
        """
        The number of days in this StatsRange.
        """
        delta = self.end_date - self.start_date
        return delta.days + 1

    @classmethod
    def get_period(cls, date, frequency):
        if frequency == 'DAILY':
            return cls.get_one_day_period(date)
        if frequency == 'WEEKLY':
            return cls.get_one_week_period(date)
        if frequency == 'MONTHLY':
            return cls.get_one_month_period(date)

    @classmethod
    def get_previous_period(cls, current_period, frequency):
        if frequency == 'DAILY':
            previous_date = current_period.start_date - timedelta(days=1)
            return cls.get_one_day_period(previous_date)
        if frequency == 'WOW_DAILY':
            previous_date = current_period.start_date - timedelta(days=7)
            return cls.get_one_day_period(previous_date)
        if frequency == 'WEEKLY':
            previous_date = current_period.end_date - timedelta(days=7)
            return cls.get_one_week_period(previous_date)
        if frequency == 'MONTHLY':
            previous_start = subtract_one_month(current_period.start_date)
            previous_end = current_period.start_date - timedelta(days=1)
            return cls("Previous Month", previous_start, previous_end)

    @classmethod
    def get_one_day_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One day", date, date)

    @classmethod
    def get_one_week_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One week", date-timedelta(days=6), date)

    @classmethod
    def get_one_month_period(cls, date):
        """
        Return instantiated one day period for date.
        """
        return cls("One month", subtract_one_month(date), date - timedelta(days=1))
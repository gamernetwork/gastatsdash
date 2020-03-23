from datetime import datetime, timedelta, date
import io
import pygal


def format_data_rows(results):
    """
    Returns results from analytics as a list of dictionaries with key/value
    pairs organised by column headers.

    Args:
        * `data` - `dict` - The analytics data for a view.

    Returns:
        * `dict`
    """
    output = []
    # NOTE are these checks really necessary? Is rows an empty list when empty?
    rows = results.get('rows', [])
    column_headers = results.get('columnHeaders', [])
    for row in rows:
        data = {}
        for count, column in enumerate(column_headers):
            data[column['name']] = row[count]
        output.append(data)
    return output


def convert_to_floats(row, metrics):
    """
    Converts the values of each metrics to float for a given row.

    Args:
        * `row` - `dict` - The data to be converted.
        * `metrics` - `list` - The metrics for which the values need to be
          converted.

    Returns:
        * `dict`
    """
    for metric in metrics:
        if metric in row:
            row[metric] = float(row[metric])
        else:
            row[metric] = 0.0
    return row


def sig_fig(sf, num):
    condensed_num = "%0.*g" % ((sf), num)
    return float(condensed_num)


# TODO test
def change_key_names(data, changes):
    """
    Renames the keys specified in rows.
    """
    for original, new in changes:
        data[new] = data.pop(original)
    return data


# TODO test
def prefix_keys(data, prefix):
    """
    Adds a prefix to every key in a dict.

    Args:
        * `data` - `dict`
        * `prefix` - `string` - string to be prefixed to every key in `data`.

    Returns:
        * `dict`
    """
    return {prefix + k: v for k, v in data.items()}

# TODO test
def remove_prefix_from_keys(data, prefix):
    """
    Removed the `prefix` from each key in `data`.

    Args:
        * `data` - `dict` - An analytics data blob.
        * `prefix` - `string` - The prefix to be removed from each key.

    Returns:
        * `dict`
    """
    keys = list(data.keys())
    for key in keys:
        assert key.startswith(prefix)
        new_key = key[3:]
        data[new_key] = data.pop(key)
    return data


def percentage(change, total):
    try:
        percentage = (change / float(total)) * 100
    except ZeroDivisionError:
        percentage = 0
    return percentage



def rate_per_1000(metric, comparative):
    try:
        rate = metric / float(comparative / 1000.0)
    except ZeroDivisionError:
        rate = 0
    return rate

# TODO test
def sort_data(unsorted_list, metric, limit=10000, reverse=True):
    """
    Sorts a list of dictionaries by the 'metric' key given.

    Args:
        * `unsorted_list` - `list` - list of dicts to be sorted.
        * `metric` - `string` - key by which to sort the dicts.
        * `[limit]` - `int` - Max number of dict that wil be included in the
          resulting list
        * `[reverse]` - `bool` - Whether the sorting should be reversed.
    """
    sorted_list = sorted(unsorted_list, key=lambda k: k[metric],
                         reverse=reverse)
    top_results = sorted_list[:limit]
    return top_results


def list_search(to_search, key, value):
    """
    Given a list of dictionaries, returns the dictionary that matches the given
    key value pair.
    """
    result = [element for element in to_search if element[key] == value]
    if result:
        return result[0]
    else:
        raise KeyError



def aggregate_data(data, aggregate_keys, match_key=None):
    """
    Aggregates data given. Returns dictionary of all metrics aggregated.

    Args:
        * `data` - `list` - The data rows to be aggregated.
        * `aggregate_keys` - `list` - Metrics to be aggregated.

    Returns:
        * `list`
    """
    # TODO finish docstrings.
    if match_key:
        return aggregate_data_by_match_key(data, aggregate_keys, match_key)
    new_table = {}
    for row in data:
        for key in aggregate_keys:
            if key in new_table:
                new_table[key] += row[key]
            else:
                new_table[key] = row[key]
    if new_table:
        return [new_table]
    return None


# TODO this method returns a list and the other method returns a dict. Should be consistent
def aggregate_data_by_match_key(data, aggregate_keys, match_key):
    """
    Aggregates data given by a match key.
    """
    new_table = []
    for row in data:
        try:
            result = list_search(new_table, match_key, row[match_key])
            for key in aggregate_keys:
                result[key] += row[key]
        except KeyError:
            new_table.append(row)
    return new_table


# TODO add matchkey functionality
def get_change(data_a, data_b, change_keys, match_key=None):
    """
    Given two sets of data, gets the change and percentage change between the
    two data sets for each of the given `change_keys`. Also includes the
    actual/figure value of `data_b`.

    Args:
        * `data_a` - `dict` - The first data set being compared.
        * `data_b` - `dict` - The second data set being compared.
        * `change_keys` - `list` - A list of strings. The two data sets are
          compared by these metrics.

    Returns:
        * `dict`
    """
    result = {}
    for key in change_keys:
        result['figure_%s' % (key)] = data_b[key]
        result['change_%s' % (key)] = data_a[key] - data_b[key]
        result['percentage_%s' % (key)] = percentage(
            result['change_%s' % (key)],
            data_b[key]
        )
    return result


def convert_values_list(id_dict):
    """
    Converts the values of a dictionary to be list format
    """
    # NOTE wtf?
    for key in id_dict:
        try:
            converted = id_dict[key].split()
        except AttributeError:
            converted = id_dict[key]
        id_dict[key] = converted
    return id_dict


def chart(title, x_labels, data, x_title, y_title):
    line_chart = pygal.Line(height=500, interpolate='cubic',
                            x_label_rotation=30, stroke_style={"width": 2})
    line_chart.title = title
    line_chart.x_title = x_title
    line_chart.y_title = y_title
    line_chart.x_labels = x_labels
    for line in data:
        line_chart.add(line, data[line])

        # NOTE disabled for the moment.
    # imgdata = io.StringIO()
    # image = line_chart.render_to_png(imgdata)
    # imgdata.seek(0)
    # return imgdata.buf

    # line_chart.render_to_png("/var/www/dev/faye/statsdash_reports/social.png")


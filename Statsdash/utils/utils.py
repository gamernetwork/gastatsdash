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


def change_key_names(rows, changes):
    """
    Renames the keys specified in rows
    Where changes = {new:original, new:original}
    """
    for row in rows:
        for new, original in changes.items():
            row[new] = row.pop(original)
    return rows


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


def sort_data(unsorted_list, metric, limit=10000, reverse=True):
    """
    Sorts a list of dictionaries by the "metric" key given
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



def aggregate_data(data, aggregate_keys, match_key):
    """
    Aggregates data given. Returns dictionary of all metrics aggregated.

    Args:
        * `data` - `list` - The data rows to be aggregated.
        * `aggregate_keys` - `list` - Metrics to be aggregated.

    Returns:
        * `dict`
    """
    if match_key:
        return aggregate_data_by_match_key(data, aggregate_keys, match_key)
    new_table = {}
    for row in data:
        for key in aggregate_keys:
            if key in new_table:
                new_table[key] += row[key]
            else:
                new_table[key] = row[key]
    return new_table


def aggregate_data_by_match_key(table, aggregate_keys, match_key):
    """
    Aggregates data given by a match key.
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


def add_change(this_period, previous_period, change_keys, label,
               match_key=None):
    """
    Adds change data to current period data structure, either by dimension or
    not.
    """
    # TODO improve docstring.
    if match_key:
        for row in this_period:
            try:
                result = list_search(previous_period, match_key,
                                     row[match_key])
                for key in change_keys:
                    row['%s_figure_%s' % (label, key)] = result[key]
                    row['%s_change_%s' % (label, key)] = row[key] - result[key]
                    row['%s_percentage_%s' % (label, key)] = percentage(
                        row['%s_change_%s' % (label, key)], result[key])
            except KeyError:
                for key in change_keys:
                    row['%s_figure_%s' % (label, key)] = 0
                    row['%s_change_%s' % (label, key)] = 0
                    row['%s_percentage_%s' % (label, key)] = 0
    else:
        for key in change_keys:
            try:
                this_period['%s_figure_%s' % (label, key)] = previous_period[
                    key]
                this_period['%s_change_%s' % (label, key)] = this_period[key] - \
                                                             previous_period[
                                                                 key]
                this_period['%s_percentage_%s' % (label, key)] = percentage(
                    this_period['%s_change_%s' % (label, key)],
                    previous_period[key])
            except KeyError:
                this_period['%s_figure_%s' % (label, key)] = 0
                this_period['%s_change_%s' % (label, key)] = 0
                this_period['%s_percentage_%s' % (label, key)] = 0

    return this_period


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

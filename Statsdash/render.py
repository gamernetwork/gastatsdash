from jinja2 import Environment, PackageLoader, select_autoescape


# TODO add tests for render


# custom filters
def int_comma(value):
    """
    Converts an integer to a string containing commas every three digits
    """
    return '{:,}'.format(value)


def cut(word, part="www."):
    """
    Where word is a string
    Removes the section specified by part
    """
    split = word.split(part)
    truncated = "".join(split)
    return truncated 


def div_or_na(num, denom):
    if float(denom) > 0:
        return float(num) / float(denom)
    else:
        return "N/A"


def get_environment():
    """
    Returns Jinja2 rendering environment and creates context with custom
    filters.
    """
    env = Environment(
        loader=PackageLoader('Statsdash', 'Templates'),
        autoescape=select_autoescape(['html', 'xml']),
        extensions=['jinja2.ext.loopcontrols']
    )
    env.filters['intcomma'] = int_comma
    env.filters['cut'] = cut
    env.globals['div_or_na'] = div_or_na
    return env

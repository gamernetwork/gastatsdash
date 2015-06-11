import os
import pynliner

from django.template import Context
import django.template.loader
import django.template
import django.conf

import django


cwd=os.path.dirname(os.path.realpath(__file__))
django.conf.settings.configure( TEMPLATE_DIRS=(os.path.join(cwd, "templates"),), INSTALLED_APPS=['django.contrib.humanize'] )

django.setup()

register = django.template.Library()
@register.filter
def as_percentage_of(part, whole):
    try:
        return "%0.1f%%" % (float(part) / whole * 100)
    except (ValueError, ZeroDivisionError):
        return ""

@register.filter
def pages_per_visitor(part, whole):
    try:
        return "%0.1f" % (float(part) / whole)
    except (ValueError, ZeroDivisionError):
        return "%%Err%%"

django.template.builtins.append(register)

def render_template(template_name, context, email=True):
    """
    Helper function for rendering template given a context.
    """
    template = django.template.loader.get_template(template_name)
    c = Context(context)
    html = template.render(c)
    
    if email:
        return pynliner.fromString(html)
    else:
        return html

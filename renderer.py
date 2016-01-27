import os
import pynliner

from django.template import Context
import django.template.loader
import django.template
import django.conf

import django
from django.template.defaultfilters import stringfilter

cwd=os.path.dirname(os.path.realpath(__file__))
django.conf.settings.configure( TEMPLATE_DIRS=(os.path.join(cwd, "templates"),), INSTALLED_APPS=['django.contrib.humanize'], TEMPLATE_DEBUG=True )

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

@register.filter(is_safe=True)
@stringfilter
def get_report_change(value):
  	if value == 'daily':
  		  return 'WoW'
  	elif value == 'monthly':
  		  return 'MoM'    



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

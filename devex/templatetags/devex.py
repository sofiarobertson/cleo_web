from django import template
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters import HtmlFormatter

from django.utils.safestring import mark_safe


register = template.Library()

@register.filter
def highlight_python(value):

    return mark_safe(highlight(value, PythonLexer(), HtmlFormatter()))

@register.filter
def degrees_to_ra(degrees):
    ra_hours = int((degrees // 15))
    remaining = degrees % 15
    minutes_decimal = remaining * 4
    minutes = int(minutes_decimal)
    remaining_minutes_decimal = minutes_decimal % 1
    seconds_decimal = remaining_minutes_decimal * 60
    seconds = (seconds_decimal)

    ra = (f"{ra_hours}:{minutes}:{seconds:.2f}")
    return f"{ra}"

@register.filter
def degrees_to_dec(degrees):
    dec_degrees = abs(degrees)
    degrees_int = int(dec_degrees)
    arcminutes = int((dec_degrees - degrees_int) * 60)
    arcseconds = (dec_degrees - degrees_int - arcminutes / 60) * 3600

    dec = f"{degrees_int}:{arcminutes}:{arcseconds:.2f}"

    return f"{dec}"

@register.filter
def seconds_to_hours(seconds):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
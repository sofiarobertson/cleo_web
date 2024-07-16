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
def degrees_to_ra(degrees:float):
    ra_hours = int((degrees / 15.0))
    minutes = int(((ra_hours) * 60.0))
    seconds = ((ra_hours - minutes / 60.0) * 3600.0)

    ra = (f"{ra_hours}: {minutes}: {seconds}")
    return f'{ra}'



# def degrees_to_dec(degrees):
#     dec_degrees = abs(degrees)
#     degrees_int = int(dec_degrees)
#     arcminutes = int((dec_degrees - degrees_int) * 60)
#     arcseconds = (dec_degrees - degrees_int - arcminutes / 60) * 3600
#     sign = '+' if degrees >= 0 else '-'

#     dec = f"{sign}{degrees_int}° {arcminutes}' {arcseconds:.2f}\""

#     return dec
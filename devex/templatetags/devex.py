from django import template
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters import HtmlFormatter

from django.utils.safestring import mark_safe


register = template.Library()

@register.filter
def highlight_python(value):
    return mark_safe(highlight(value, PythonLexer(), HtmlFormatter()))
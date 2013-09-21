from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='show_if_gt', is_safe=True)
@stringfilter
def show_if_gt(value, compare_value):
    """show if greater than a num"""
    if int(value) > compare_value:
        return value
    else:
        return ""


from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='ul_addclass', is_safe=True)
@stringfilter
def ul_addclass(value, classnames):
    """adds class(es) to ul tag"""
    attribute = 'class="{0}"'.format(classnames)
    return value.replace('<ul', '<ul ' + attribute)


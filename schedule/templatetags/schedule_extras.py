from datetime import datetime

from django import template

register = template.Library()


@register.filter()
def index(value, index):
    return value[index]


@register.filter()
def width(value):
    return 95 / len(value)


@register.filter()
def back_to_date(value):
    return datetime.strptime(value, '%Y-%m-%d')

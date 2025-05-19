from django import template
from datetime import date

register = template.Library()

@register.filter(name='calculate_age')
def calculate_age(dob):
    """Calculate age from date of birth"""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

@register.filter(name='get_attribute')
def get_attribute(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    try:
        if hasattr(obj, str(attr)):
            return getattr(obj, str(attr))
        elif hasattr(obj, 'get'):
            return obj.get(str(attr))
        else:
            return None
    except (TypeError, AttributeError):
        return None 
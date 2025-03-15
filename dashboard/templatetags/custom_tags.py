from django import template

register = template.Library()

@register.filter
def range_filter(value):
    return range(value)


@register.filter
def get_item(list, index):
    """Access a list element by index."""
    try:
        return list[index]
    except (IndexError, TypeError):
        return None

@register.filter
def get_image_url(product_image):
    """Get the URL of a product image."""
    if product_image and hasattr(product_image, 'image'):
        return product_image.image.url
    return ''

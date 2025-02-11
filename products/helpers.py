from django.core.paginator import Paginator

def get_paginated_products(request, queryset, per_page=8):
    """
    Helper function to paginate products and include their first image.
    """
    paginator = Paginator(queryset, per_page)  # Paginate the queryset
    page_number = request.GET.get('page')  # Get the current page number
    page_obj = paginator.get_page(page_number)  # Get the Page object for the current page

    # Add the first image for each product
    products_with_images = [
        {
            'product': product,
            'image': product.images.first().image.url if product.images.first() else None,
        }
        for product in page_obj.object_list
    ]

    return products_with_images, page_obj

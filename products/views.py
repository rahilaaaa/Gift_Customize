from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponseRedirect
from .models import Product, Category,Review,CustomizationOption,ProductCustomization
from orders.models import Cart,Wishlist
from .helpers import get_paginated_products
from django.http import JsonResponse
from django.views.decorators.cache import cache_control,never_cache
from django.db.models import Avg
from django.contrib.contenttypes.models import ContentType
from .models import Offer
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control, never_cache
from users.decorators import user_required


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='login_user')
def home(request):
    high_priority_products = Product.objects.filter(priority='high',  is_active=True).order_by('-id')
    products_with_images, page_obj = get_paginated_products(request, high_priority_products, per_page=8)

    cart_count = 0
    wishlist_count = 0

    if request.user.is_authenticated:
        cart = Cart.objects.filter(customer=request.user).first()
        cart_count = cart.items.count() if cart else 0
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0

    response = render(request, 'products/home.html', {
        'products_with_images': products_with_images,
        'page_obj': page_obj,
        'username': request.user.username,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    })

    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


def product_details(request, pk):
    product = get_object_or_404(Product, id=pk)
    product_images = product.images.all()
    product_variants = product.variants.all()
    reviews = product.reviews.all()

    # Check for product-specific offer
    product_content_type = ContentType.objects.get_for_model(Product)
    product_offer = Offer.objects.filter(content_type=product_content_type, object_id=product.id, status='active').first()

    # Check for category-specific offer if no product-specific offer exists
    category_offer = None
    if not product_offer:
        category_content_type = ContentType.objects.get_for_model(Category)
        category_offer = Offer.objects.filter(content_type=category_content_type, object_id=product.category.id, status='active').first()

    # Determine the final offer to apply
    final_offer = product_offer or category_offer

    # Calculate the discounted price if an offer is available
    discounted_price = None
    if final_offer:
        discounted_price = product.price * (1 - final_offer.offer_percentage / 100)

    if request.method == "POST":
        # Handle review submission
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if the request is AJAX
            name = request.POST.get("name")
            email = request.POST.get("email")
            rating = request.POST.get("rating")
            review_text = request.POST.get("review_text")

            if name and email and rating and review_text:
                Review.objects.create(
                    product=product,
                    name=name,
                    email=email,
                    rating=rating,
                    review_text=review_text,
                )
                return JsonResponse({"success": True})

            return JsonResponse({"success": False, "error": "All fields are required."})
        
        elif request.FILES.get("image"):
            uploaded_image = request.FILES["image"]

            # Create a new ProductCustomization entry for the uploaded image
            ProductCustomization.objects.create(
                product=product,
                customer=request.user,  # Use request.user directly
                customization_image=uploaded_image,
            )
    # Fetch related products of the same category
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True  # Only active products
    ).exclude(id=product.id)

    # Add the first image for each related product
    related_products_with_images = [
        {
            'product': related_product,
            'image': related_product.images.first().image.url if related_product.images.first() else None,
        }
        for related_product in related_products
    ]

    if request.user.is_authenticated:
        cart = Cart.objects.filter(customer=request.user).first()
        cart_count = cart.items.count() if cart else 0
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0

    else:
        cart_count = 0
        wishlist_count = 0

    context = {
        'product': product,
        'product_images': product_images,
        'product_variants': product_variants,
        'related_products_with_images': related_products_with_images,
        'reviews': reviews,
        'username': request.user.username,
        'cart_count': cart_count,  # Add cart count to context
        'wishlist_count': wishlist_count,  # Add wishlist count to context
        'final_offer': final_offer,  # Add final offer to context
        'discounted_price': discounted_price,  # Add discounted price to context


    }



    # Dynamically select the template based on the category name
    if product.category and product.category.name == '3d crystal':
        template = 'products/3d_crystal_product_details.html'
    elif product.category and product.category.name == 'wallet':
        template = 'products/wallet.html'
    elif product.category and product.category.name == 'water bottle':
        template = 'products/bottle.html'
    else:
        template = 'products/product_details.html'  # Default template

    return render(request, template, context)



# def upload_image(request, product_id):
#     if request.method == "POST" and request.FILES.get("image"):
#         # Get the product object
#         product = get_object_or_404(Product, id=product_id)
        
#         # Ensure the user is authenticated
#         if not request.user.is_authenticated:
#             return JsonResponse({"error": "User must be logged in to upload an image."}, status=403)
        
#         # Get the uploaded file
#         uploaded_image = request.FILES["image"]

#         # Save the customization
#         customization = ProductCustomization.objects.create(
#             product=product,
#             customer=request.user,
#             customization_image=uploaded_image
#         )
        
#         # Return success response
#         return JsonResponse({"success": True, "message": "Image uploaded successfully."})
    
#     return JsonResponse({"error": "Invalid request."}, status=400) 



def submit_review(request, pk):
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        product = get_object_or_404(Product, id=pk)
        name = request.POST.get("name")
        email = request.POST.get("email")
        rating = request.POST.get("rating")
        review_text = request.POST.get("review_text")

        if name and email and rating and review_text:
            review = Review.objects.create(
                product=product,
                name=name,
                email=email,
                rating=rating,
                review_text=review_text,
            )
            return JsonResponse({
                "success": True,
                "review": {
                    "name": review.name,
                    "created_at": review.created_at.strftime("%d %b %Y"),
                    "rating": review.rating,
                    "review_text": review.review_text,
                }
            })

        return JsonResponse({"success": False, "error": "All fields are required."})
    return JsonResponse({"success": False, "error": "Invalid request."})


def shop(request):
    # Fetch all categories for the category filter
    categories = Category.objects.all()

    selected_category = request.GET.get('category', 'all')  # Default to 'all'
    sort_by = request.GET.get('sort', 'latest')  # Default to 'latest' if no sort is selected
    search_query = request.GET.get('search', '')  # Capture search term from the query parameters

    # Filter products by category and is_active
    if selected_category == 'all':
        products = Product.objects.filter(is_active=True)
    else:
        category = get_object_or_404(Category, name=selected_category)
        products = Product.objects.filter(category=category, is_active=True)
    # Apply search filter if there is a search query
    if search_query:
        products = products.filter(title__icontains=search_query)  # Filter by product name

 # Apply sorting based on the sort parameter
    if sort_by == 'latest':
        products = products.order_by('-created_at')  # Sort by creation date, most recent first
    elif sort_by == 'low_to_high':
        products = products.order_by('price')  # Sort by price low to high
    elif sort_by == 'high_to_low':
        products = products.order_by('-price')  # Sort by price high to low
    elif sort_by == 'featured':
        products = products.filter(priority='high')  # Filter by featured products
    elif sort_by == 'average_rating':
        products = products.annotate(average_rating=Avg('reviews__rating')).order_by('-average_rating')  # Sort by average rating
    elif sort_by == 'a_to_z':
        products = products.order_by('title')  # Sort by title A-Z
    elif sort_by == 'z_to_a':
        products = products.order_by('-title')  # Sort by title Z-A

    # Get paginated products
    products_with_images, page_obj = get_paginated_products(request, products, per_page=8)

    # Calculate cart count
    if request.user.is_authenticated:
        cart = Cart.objects.filter(customer=request.user).first()
        cart_count = cart.items.count() if cart else 0
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0
    else:
        cart_count = 0
        wishlist_count = 0


    return render(request, 'products/shop.html', {
        'products_with_images': products_with_images,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'categories': categories,  # Pass available categories to the template
        'sort_by': sort_by,  # Pass the current sorting option to the template
        'search_query': search_query,  # Pass search query to the template
        'cart_count': cart_count,  # Add cart count to context
        'wishlist_count': wishlist_count,  # Add wishlist count to context

    })

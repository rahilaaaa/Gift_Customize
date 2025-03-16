from django.shortcuts import render, redirect,get_object_or_404
from products.models import Product, ProductVariant, ProductImage,Review,Coupon
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout
from datetime import datetime
from django.core.files.base import ContentFile
import base64
from django.core.files.uploadedfile import InMemoryUploadedFile
import json
from django.contrib.auth import get_user_model
from django.views.decorators.cache import never_cache
from products.models import Category,Offer
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.images import get_image_dimensions
from PIL import Image
from io import BytesIO
from django.conf import settings
from django.db.models import Q
from orders.models import Order, OrderItem
from django.db import transaction
from .forms import CouponForm
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal, InvalidOperation
from django.contrib.contenttypes.models import ContentType
from users.models import ReferralOffer
from django.db.models import Sum, F,Case, When, DecimalField
from django.utils.dateparse import parse_date
from datetime import timedelta, date
from django.http import HttpResponse
from django.db.models.functions import TruncDate
from django.utils.timezone import make_aware
from django.template.loader import render_to_string
from django.db.models.functions import Concat
from weasyprint import HTML
import tempfile
from django.db.models import Sum, Count,OuterRef, Subquery,F, Value
import xlwt
import io
import logging
import os
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from users.models import Wallet
from django.core.exceptions import ValidationError
from dashboard.decorators import admin_required


logger = logging.getLogger(__name__)

# Function to check if a user is a superuser
def is_superuser(user):
    return user.is_superuser


@never_cache
def login_admin(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('dashboard')  # Redirect superusers to the admin panel
    
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return render(request, 'admin/login.html', {'error': 'Email and password are required.'})

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_superuser:
                # Set session key for admins
                request.session['admin_auth'] = True  
                auth_login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'admin/login.html', {'error': 'Access restricted to superusers.'})
        else:
            return render(request, 'admin/login.html', {'error': 'Invalid email or password. Please try again.'})

    return render(request, 'admin/login.html')



@login_required(login_url='logout_admin')
@user_passes_test(is_superuser, login_url='logout_admin')
def admin(request):
    # Get query parameters
    start_date = request.GET.get("startDate")
    end_date = request.GET.get("endDate")
    predefined_range = request.GET.get("predefinedRange")

    today = date.today()

    # Handle predefined date ranges
    if predefined_range:
        if predefined_range == "oneDay":
            start_date, end_date = today - timedelta(days=1), today
        elif predefined_range == "oneWeek":
            start_date, end_date = today - timedelta(weeks=1), today
        elif predefined_range == "oneMonth":
            start_date, end_date = today - timedelta(days=30), today
        elif predefined_range == "oneYear":
            start_date, end_date = today - timedelta(days=365), today
    else:
        # Convert date strings to date objects
        start_date = parse_date(start_date) if start_date else today - timedelta(days=30)
        end_date = parse_date(end_date) if end_date else today

    # Ensure dates are timezone-aware
    start_date = make_aware(datetime.combine(start_date, datetime.min.time()))
    end_date = make_aware(datetime.combine(end_date, datetime.max.time()))

    # Filter orders based on date range
    orders = Order.objects.filter(created_at__range=[start_date, end_date]).order_by('-created_at')


    # Compute total sales
    total_sales_count = orders.count()
    total_order_amount = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0

      # Compute discount per order (Coupon + Offer)
    for order in orders:
        order_items = OrderItem.objects.filter(order=order)

        coupon_discount = order_items.filter(coupon__isnull=False).annotate(
            discount_applied=Case(
                When(coupon__discount_type='percent', then=F('price') * F('coupon__discount_value') / 100),
                When(coupon__discount_type='fixed', then=F('coupon__discount_value')),
                default=0,
                output_field=DecimalField()
            )
        ).aggregate(total_coupon_discount=Sum('discount_applied'))['total_coupon_discount'] or 0

        offer_discount = 0
        for item in order_items:
            product = item.product
            product_offer = Offer.objects.filter(
                content_type=ContentType.objects.get_for_model(product),
                object_id=product.id,
                status='active'
            ).first()

            category_offer = Offer.objects.filter(
                content_type=ContentType.objects.get_for_model(product.category),
                object_id=product.category.id,
                status='active'
            ).first()

            highest_discount = 0
            if product_offer:
                highest_discount = max(highest_discount, product_offer.offer_percentage)
            if category_offer:
                highest_discount = max(highest_discount, category_offer.offer_percentage)

            if highest_discount > 0:
                offer_discount += (item.price * highest_discount / 100) * item.quantity

        # Save total discount in the order
        order.total_discount = coupon_discount + offer_discount
        order.save()  # Save to the database

    # Sales data for chart
    sales_data = orders.annotate(date=TruncDate('created_at')).values('date').annotate(
        total_sales=Count('id'),
        revenue=Sum('total_price')
    ).order_by('date')

    dates = [entry['date'].strftime('%Y-%m-%d') for entry in sales_data]
    total_sales = [entry['total_sales'] for entry in sales_data]
    revenue = [float(entry['revenue']) for entry in sales_data]
    # Compute overall discount
    total_discount = sum(order.total_discount for order in orders)

    # Pass data to template
    context = {
        "orders": orders,
        "total_sales_count": total_sales_count,
        "total_discount": total_discount,
        "total_order_amount": total_order_amount,
        "sales_dates": json.dumps(dates),
        "sales_counts": json.dumps(total_sales),
        "sales_revenue": json.dumps(revenue),
    }
    return render(request, 'admin/index.html', context) 




# def export_orders_excel(request):
#     """Export filtered orders as an Excel file."""
#     orders = get_filtered_orders(request)

#     output = io.BytesIO()
#     workbook = xlsxwriter.Workbook(output)
#     worksheet = workbook.add_worksheet()

#     # Define headers
#     headers = ["Order ID", "Customer", "Total Price", "Created At", "Total Discount"]
#     for col_num, header in enumerate(headers):
#         worksheet.write(0, col_num, header)

#     # Write order data
#     for row_num, order in enumerate(orders, start=1):
#         worksheet.write(row_num, 0, order.id)
#         worksheet.write(row_num, 1, str(order.customer))  # Assuming order has a customer field
#         worksheet.write(row_num, 2, order.total_price)
#         worksheet.write(row_num, 3, order.created_at.strftime("%Y-%m-%d"))
#         worksheet.write(row_num, 4, calculate_total_discount(order))

#     workbook.close()
#     output.seek(0)

#     response = HttpResponse(output, content_type="application/vnd.ms-excel")
#     response["Content-Disposition"] = 'attachment; filename="orders.xlsx"'
#     return response

def logout_admin(request):
    if 'admin_auth' in request.session:
        del request.session['admin_auth']  # Clear admin session key
    if 'user_auth' in request.session:
        del request.session['user_auth']  # Clear user session key
    logout(request)
    return redirect('login_admin')

def reviews(request):
    # Get the search query from the request
    search_query = request.GET.get('search', '')

    # Filter reviews based on the search query (search by product name or reviewer name)
    if search_query:
        reviews = Review.objects.filter(
            product__title__icontains=search_query) | Review.objects.filter(name__icontains=search_query)
    else:
        reviews = Review.objects.all()

    # Calculate filled and empty stars for each review
    for review in reviews:
        review.filled_stars = [True] * review.rating  # List of 'True' for filled stars
        review.empty_stars = [False] * (5 - review.rating)  # List of 'False' for empty stars

    return render(request, 'admin/review/page-reviews.html', {'reviews': reviews, 'search_query': search_query})

def review_details(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    return render(request, 'admin/review/review_details.html', {'review': review})


def products(request):
    # Get the selected category from the query parameters
    selected_category = request.GET.get('category', 'all')
    selected_date = request.GET.get('date', None)  # Get selected date if provided
    
    # Fetch products based on the selected category
    products = Product.objects.prefetch_related('images').filter(is_active=True)

    
    if selected_category != 'all':
        # Use the actual category object for filtering
        category = Category.objects.filter(name=selected_category).first()
        if category:
            products = products.filter(category=category)
    
    if selected_date:  # If a date is selected, filter products by creation date
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
            products = products.filter(created_at__date=date_obj)
        except ValueError:
            pass  # If the date is not valid, no filter is applied
    
    context = {
        'categories': Category.objects.all(),  # Fetch categories from the database
        'selected_category': selected_category,
        'selected_date': selected_date,
        'products': [
            {
                'id': product.id,
                'title': product.title,
                'price': product.price,
                'category': product.category,
                'image': product.images.first().image.url if product.images.exists() else None,
            }
            for product in products
        ]
    }
    return render(request, 'admin/product/product_list.html', context)




def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_images = ProductImage.objects.filter(product=product)
    product_variants = ProductVariant.objects.filter(product=product)

    if request.method == 'POST':
        # Retrieve form data
        title = request.POST.get('title')
        priority = request.POST.get('priority')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_name = request.POST.get('product_category')

        # Validate required fields
        required_fields = {
            'Title': title,
            'Priority': priority,
            'Description': description,
            'Price': price,
            'Product Category': category_name,
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            for field in missing_fields:
                messages.error(request, f"{field} is required.")
            return redirect('edit_product', product_id=product_id)

        # Validate price is a positive integer
        try:
            price = float(price)
            if price <= 0:
                raise ValueError("Price must be a positive number.")
        except ValueError as e:
            messages.error(request, f"Invalid price: {str(e)}")
            return redirect('edit_product', product_id=product_id)

        # Validate priority is one of the allowed choices
        if priority not in [Product.LOW, Product.MEDIUM, Product.HIGH]:
            messages.error(request, "Invalid priority value.")
            return redirect('edit_product', product_id=product_id)

        # Check if new images are uploaded
        new_images = [request.FILES.get(f'image{i}') for i in range(1, 4)]
        has_new_images = any(new_images)

        # If new images are uploaded, validate and process them
        if has_new_images:
            for i, image in enumerate(new_images, start=1):
                if image:  # Only process if a new image is uploaded
                    try:
                        img = Image.open(image)
                        if img.format not in ['JPEG', 'PNG']:
                            raise ValueError("Invalid image format. Only JPEG and PNG are allowed.")
                        
                        width, height = img.size
                        if width > 800 or height > 800:  # Resize if dimensions exceed 800x800
                            img.thumbnail((800, 800))
                            buffer = BytesIO()
                            img.save(buffer, format='JPEG')
                            image.file = InMemoryUploadedFile(
                                buffer, None, image.name, 'image/jpeg', buffer.getbuffer().nbytes, None
                            )

                        # Update the corresponding product image
                        product_image = product_images[i-1] if i <= len(product_images) else ProductImage(product=product)
                        product_image.image = image
                        product_image.save()
                    except Exception as e:
                        messages.error(request, f"Invalid image file for image {i}: {str(e)}")
                        return redirect('edit_product', product_id=product_id)

        # Get the Category instance
        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            messages.error(request, f"Category '{category_name}' not found.")
            return redirect('edit_product', product_id=product_id)

        # Update the Product instance
        try:
            product.title = title
            product.description = description
            product.priority = priority
            product.price = price
            product.category = category
            product.save()
        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
            return redirect('edit_product', product_id=product_id)

        # Update variants with size, color, liter, and viewflex
        for i in range(1, 4):  # Assuming a maximum of 3 variants
            color = request.POST.get(f'color{i}')
            size = request.POST.get(f'size{i}')
            liter = request.POST.get(f'liter{i}')
            quantity = request.POST.get(f'quantity{i}')
            charm = request.POST.get(f'charm{i}')
            charm_img = request.FILES.get(f'charmImg{i}')
            viewflex = request.POST.get(f'viewflex{i}')

            # Only update variant if required fields are present
            if (color or size or liter) and quantity:
                try:
                    quantity = int(quantity)
                    if quantity < 0:
                        raise ValueError("Quantity must be a non-negative integer.")

                    # Get or create variant
                    variant = product_variants[i-1] if i <= len(product_variants) else ProductVariant(product=product)
                    variant.color = color
                    variant.size = size
                    variant.liter = liter
                    variant.quantity = quantity
                    variant.charm = charm
                    variant.charmImg = charm_img
                    variant.viewflex = viewflex

                    # Apply category-specific rules
                    if category.name.lower() == "wallet":
                        variant.size = None
                        variant.liter = None
                    elif category.name.lower() == "3d_crystal":
                        variant.color = None
                        variant.liter = None
                        variant.charm = None
                        variant.charmImg = None

                    variant.save()
                except ValueError as ve:
                    messages.error(request, f"Invalid quantity for variant {i}: {str(ve)}")
                except Exception as e:
                    logger.error(f"Error updating variant {i}: {str(e)}")
                    messages.error(request, f"Error updating variant {i}: {str(e)}")

        messages.success(request, "Product updated successfully.")
        return redirect('products')

    # Render the edit product form with existing data
    return render(request, 'admin/product/edit_product.html', {
        'product': product,
        'product_images': product_images,
        'product_variants': product_variants,
    })


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False  # Soft delete
    product.save()
    messages.success(request, f"Product '{product.title}' has been removed successfully.")
    return redirect('products')  # Redirect to product list

@user_passes_test(is_superuser, login_url='login_admin')
def add_products(request):
    if request.method == 'POST':
        # Retrieve form data
        title = request.POST.get('title')
        priority = request.POST.get('priority')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_name = request.POST.get('product_category')

        # Validate required fields
        required_fields = {
            'Title': title,
            'Priority': priority,
            'Description': description,
            'Price': price,
            'Product Category': category_name,
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            for field in missing_fields:
                messages.error(request, f"{field} is required.")
            return redirect('add_products')

        # Validate price is a positive integer
        try:
            price = int(price)
            if price <= 0:
                raise ValueError("Price must be a positive integer.")
        except ValueError as e:
            messages.error(request, f"Invalid price: {str(e)}")
            return redirect('add_products')

        # Validate at least 3 images are uploaded
        images = [request.FILES.get(f'image{i}') for i in range(1, 4)]
        if not all(images):
            messages.error(request, "Please upload exactly 3 images.")
            return redirect('add_products')

        # Validate image dimensions and resize if necessary
        for image in images:
            try:
                img = Image.open(image)
                width, height = img.size
                if width > 800 or height > 800:  # Resize if dimensions exceed 800x800
                    img.thumbnail((800, 800))
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG')
                    image.file = buffer
            except Exception as e:
                messages.error(request, f"Invalid image file: {str(e)}")
                return redirect('add_products')

        # Get the Category instance
        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            messages.error(request, f"Category '{category_name}' not found.")
            return redirect('add_products')

        # Create and save the Product instance
        try:
            product = Product(
                title=title,
                description=description,
                priority=priority,
                price=price,
                category=category,
            )
            product.save()
        except Exception as e:
            messages.error(request, f"Error saving product: {str(e)}")
            return redirect('add_products')

        # Save images
        for i, image in enumerate(images, start=1):
            try:
                product_image = ProductImage(product=product, image=image)
                product_image.save()
            except Exception as e:
                messages.error(request, f"Error saving image {i}: {str(e)}")
                return redirect('add_products')

        # Save variants with size, color,  liter and viewflex
        for i in range(1, 4):  # Assuming a maximum of 3 variants
            color = request.POST.get(f'color{i}')
            size = request.POST.get(f'size{i}')
            liter = request.POST.get(f'liter{i}')
            quantity = request.POST.get(f'quantity{i}')
            charm = request.POST.get(f'charm{i}')
            charmImg = request.FILES.get(f'charmImg{i}')
            viewflex = request.POST.get(f'viewflex{i}')
            print(f"Variant {i} - Viewflex: {viewflex}")  # Debugging line

  

            if (color or size or liter ) and quantity:
                try:
                    quantity = int(quantity)
                    if quantity < 0:
                        raise ValueError("Quantity must be a non-negative integer.")
                    variant = ProductVariant(
                        product=product,
                        color=color,
                        size=size,
                        liter=liter,
                        quantity=quantity,
                        charm=charm,
                        charmImg=charmImg,
                        viewflex=viewflex

                        
                    )
                    variant.save()
                except ValueError as ve:
                    messages.error(request, f"Invalid quantity for variant {i}: {str(ve)}")
                except Exception as e:
                    messages.error(request, f"Error saving variant {i}: {str(e)}")

        messages.success(request, "Product added successfully.")
        return redirect('add_products')

    return render(request, 'admin/product/add_products.html')  




def orders_list(request):
    # Get search query and filter parameters from the request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    order_id_search = request.GET.get('order_id', '')

    # Fetch orders based on search query and filters
    orders = Order.objects.all().order_by('-created_at')  # Order by latest first

    if search_query:
        orders = orders.filter(
            Q(customer__username__icontains=search_query) |
            Q(customer__email__icontains=search_query)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if order_id_search:
        orders = orders.filter(id__icontains=order_id_search)

    return render(request, 'admin/orders/orders_list.html', {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'order_id_search': order_id_search,
    })


@staff_member_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        if 'status' in request.POST:
            # Update the order status
            new_status = request.POST.get('status')
            if new_status:
                previous_status = order.status
                order.status = new_status
                order.save()

                # If the return is completed, refund to the wallet
                if new_status == Order.RETURN_COMPLETED and previous_status != Order.RETURN_COMPLETED:
                    try:
                        wallet, created = Wallet.objects.get_or_create(user=order.customer)
                        wallet.add_funds(order.total_price)
                        messages.success(request, f"₹{order.total_price} added to user's wallet.")
                    except ValidationError as e:
                        messages.error(request, f"Error updating wallet: {str(e)}")
                else:
                    messages.success(request, "Order status updated successfully.")

                return redirect('order_details', order_id=order.id)

        elif 'return_action' in request.POST:
            # Handle return approvals/rejections for individual items
            item_id = request.POST.get('item_id')
            action = request.POST.get('return_action')

            item = get_object_or_404(OrderItem, id=item_id)

            if action == 'approve':
                item.approve_return()
                # Refund the price of the approved item to the wallet
                try:
                    wallet, created = Wallet.objects.get_or_create(user=order.customer)
                    wallet.add_funds(item.price)
                    messages.success(request, f"Return approved for {item.product.title}. ₹{item.price} refunded to user's wallet.")
                except ValidationError as e:
                    messages.error(request, f"Error updating wallet: {str(e)}")
                    
            elif action == 'reject':
                item.reject_return()
                messages.error(request, f"Return rejected for {item.product.title}.")

            return redirect('order_details', order_id=order.id)

    order_items = OrderItem.objects.filter(order=order)

    return render(request, 'admin/orders/order-details.html', {
        'order': order,
        'order_items': order_items,
    })



@never_cache
def coupon(request):
    coupons = Coupon.objects.all().order_by('-valid_from') # Fetch all coupons, ordered by validity
    return render(request, 'admin/coupon/coupon.html', {'coupons': coupons})

@never_cache
def create_coupon(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.code = coupon.code.lower()  # Convert code to lowercase

             # Check if the coupon code already exists
            if Coupon.objects.filter(code=coupon.code).exists():
                messages.error(request, 'Coupon code already exists. Please use a different code.')
                return render(request, 'admin/coupon/create_coupon.html', {
                    'form': form,
                    'products': products,
                    'categories': categories,
                })
            
            coupon.save()  # Save first to get ID

            # Add M2M relationships
            coupon.products.set(request.POST.getlist('products'))
            coupon.categories.set(request.POST.getlist('categories'))

            messages.success(request, 'Coupon created successfully!')
            return redirect('coupon')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CouponForm()

    return render(request, 'admin/coupon/create_coupon.html', {
        'form': form,
        'products': products,
        'categories': categories,
    })


@never_cache
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon updated successfully!')
            return redirect('coupon')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'admin/coupon/edit_coupon.html', {'form': form, 'coupon': coupon})

@never_cache
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_deleted = True
    coupon.save()
    messages.success(request, 'Coupon deleted successfully!')
    return redirect('coupon')

def offer(request):
    # Fetch all offers and optimize queries using select_related and prefetch_related
    offers = Offer.objects.select_related('content_type').all()
    
    # Fetch all referral offers
    referral_offers = ReferralOffer.objects.all()

    # Render the offers.html template and pass both offers and referral_offers as context
    context = {
        'offers': offers,
        'referral_offers': referral_offers,  # Pass referral offers to the template
    }
    
    return render(request, 'admin/offers/offers.html', context)

def apply_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if offer.status == 'active':
        offer.status = 'blocked'
    else:
        offer.status = 'active'
    offer.save()
    return redirect('offers')

def edit_offers(request, offer_id):
    # Fetch the offer to be edited
    offer = get_object_or_404(Offer, id=offer_id)
    
    # Fetch the related object (Product or Category)
    if offer.content_type.model == 'product':
        related_object = Product.objects.get(id=offer.object_id)
    elif offer.content_type.model == 'category':
        related_object = Category.objects.get(id=offer.object_id)
    else:
        related_object = None

    if request.method == 'POST':
        # Extract form data
        offer_name = request.POST.get('offerName', '').strip()
        description = request.POST.get('description', '').strip()
        offer_percentage = request.POST.get('offerPercentage')

        errors = {}

        # Validate offer name
        if not offer_name:
            errors['offerName'] = 'Offer name is required'

        # Validate description
        if not description:
            errors['description'] = 'Description is required'

        # Validate percentage
        if not offer_percentage:
            errors['percentage'] = 'Percentage is required'
        else:
            try:
                percentage = float(offer_percentage)
                if not (0 < percentage <= 80):
                    errors['percentage'] = 'Percentage must be between 0.01 and 80'
            except ValueError:
                errors['percentage'] = 'Invalid percentage value'

        if errors:
            return render(request, 'admin/offers/edit_offers.html', {
                'offer': offer,
                'related_object': related_object,
                'errors': errors
            })

        # Update the offer
        try:
            offer.offer_name = offer_name
            offer.offer_description = description
            offer.offer_percentage = percentage
            offer.save()
            messages.success(request, 'Offer updated successfully!')
            return redirect('offers')  # Redirect to the offers list page
        except Exception as e:
            messages.error(request, f'Error updating offer: {str(e)}')
            return render(request, 'admin/offers/edit_offers.html', {
                'offer': offer,
                'related_object': related_object,
                'errors': {'general': 'Error updating offer'}
            })

    # GET request - display the form with current offer details
    return render(request, 'admin/offers/edit_offers.html', {
        'offer': offer,
        'related_object': related_object
    })

def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.delete()
    messages.success(request, 'Offer deleted successfully!')
    return redirect('offers')

def create_category_offers(request):
    if request.method == 'POST':
        # Get form data
        category_id = request.POST.get('category')
        offer_name = request.POST.get('offerName')
        description = request.POST.get('description')
        offer_percentage = request.POST.get('offerPercentage')
        offer_type = request.POST.get('offerType')  # Should be 'category'

        # Basic validation
        errors = {}
        
        if not category_id:
            errors['category'] = 'Please select a category'
        if not offer_name.strip():
            errors['offerName'] = 'Offer name is required'
        if not description.strip():
            errors['description'] = 'Description is required'
        if not offer_percentage:
            errors['percentage'] = 'Percentage is required'
        else:
            try:
                offer_percentage = Decimal(offer_percentage)
                if offer_percentage <= 0 or offer_percentage > 80:
                    errors['percentage'] = 'Percentage must be between 0 and 80'
            except:
                errors['percentage'] = 'Invalid percentage value'

        # Check for existing offer for this category
        try:
            category = Category.objects.get(id=category_id)
            content_type = ContentType.objects.get_for_model(Category)
            if Offer.objects.filter(content_type=content_type, object_id=category.id).exists():
                errors['category'] = 'This category already has an offer'
        except Category.DoesNotExist:
            errors['category'] = 'Invalid category selected'

        if errors:
            return render(request, 'admin/offers/create_category_offers.html', {
                'errors': errors,
                'categories': Category.objects.all()  # Pass categories again for form re-rendering
            })

        # Create the offer
        try:
            Offer.objects.create(
                content_object=category,
                offer_name=offer_name,
                offer_description=description,
                offer_percentage=offer_percentage,
                offer_type=offer_type.lower()  # Ensure lowercase
            )
            messages.success(request, 'Offer created successfully!')
            return redirect('offers')  # Replace with your offers list URL name

        except Exception as e:
            messages.error(request, f'Error creating offer: {str(e)}')
            return render(request, 'admin/offers/create_category_offers.html', {
                'errors': {'general': 'Error saving offer'},
                'categories': Category.objects.all()
            })

    # GET request - show empty form with categories
    return render(request, 'admin/offers/create_category_offers.html', {
        'categories': Category.objects.all()
    })

def create_product_offers(request):
    products = Product.objects.all()  # Fetch all products for the dropdown

    if request.method == 'POST':
        # Extract form data
        form_data = {
            'product_id': request.POST.get('product'),
            'offer_name': request.POST.get('offerName', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'offer_percentage': request.POST.get('offerPercentage'),
            'offer_type': request.POST.get('offerType', 'product')  # Default to 'product'
        }

        errors = {}
        product = None

        # Validate product
        if not form_data['product_id']:
            errors['product'] = 'Please select a product'
        else:
            try:
                product = Product.objects.get(id=form_data['product_id'])
                # Check for existing offer
                content_type = ContentType.objects.get_for_model(Product)
                if Offer.objects.filter(content_type=content_type, object_id=product.id).exists():
                    errors['product'] = 'This product already has an offer'
            except Product.DoesNotExist:
                errors['product'] = 'Invalid product selected'

        # Validate offer name
        if not form_data['offer_name']:
            errors['offerName'] = 'Offer name is required'

        # Validate description
        if not form_data['description']:
            errors['description'] = 'Description is required'

        # Validate percentage
        if not form_data['offer_percentage']:
            errors['percentage'] = 'Percentage is required'
        else:
            try:
                percentage = Decimal(form_data['offer_percentage'])
                if not (0 < percentage <= 80):
                    errors['percentage'] = 'Percentage must be between 0.01 and 80'
            except InvalidOperation:
                errors['percentage'] = 'Invalid percentage value'

        if errors:
            return render(request, 'admin/offers/create_product_offers.html', {
                'errors': errors,
                'products': products,
                'request_post': request.POST
            })

        # Create offer
        try:
            Offer.objects.create(
                content_object=product,
                offer_name=form_data['offer_name'],
                offer_description=form_data['description'],
                offer_percentage=percentage,
                offer_type=form_data['offer_type']
            )
            messages.success(request, 'Product offer created successfully!')
            return redirect('offers')  # Replace with your offers list view name

        except Exception as e:
            messages.error(request, f'Error creating offer: {str(e)}')
            return render(request, 'admin/offers/create_product_offers.html', {
                'errors': {'general': 'Error saving offer'},
                'products': products
            })

    # GET request
    return render(request, 'admin/offers/create_product_offers.html', {
        'products': products
    })

User = get_user_model()

def userlist(request):
    # Fetch users based on optional search criteria
    search_query = request.GET.get('search', '')
    
    if search_query:
        users = User.objects.filter(username__icontains=search_query, is_superuser=False)
    else:
        users = User.objects.filter(is_superuser=False)
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'admin/users/user_list.html', context)

def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    return redirect('user_list')


def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    return redirect('user_list')


# View to display all categories and add new categories
def categories(request):
   
    # If GET request, show the categories
    categories = Category.objects.all()
    return render(request, 'admin/category/categories.html', {'categories': categories})


def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip().lower()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, "Name is required.")
            return redirect('add_category')
        if not description:
            messages.error(request, "Description is required.")
            return redirect('add_category')

        if Category.objects.filter(name=name).exists():
            messages.error(request, "Category with this name already exists.")
            return redirect('add_category')

        try:
            new_category = Category(name=name, description=description)
            new_category.save()
            messages.success(request, "Category added successfully.")
        except Exception as e:
            messages.error(request, f"Error adding category: {str(e)}")

        return redirect('categories')

    return render(request, 'admin/category/create_category.html')


# View to edit category
def edit_category(request, category_id):
    # Get the category object or return 404 if it doesn't exist
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        # Get updated data from the form
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, "Name is required.")
            return redirect('edit_category', category_id=category_id)

        if Category.objects.filter(name=name).exclude(id=category_id).exists():
            messages.error(request, "Category with this name already exists.")
            return redirect('edit_categories', category_id=category_id)

        # Update the category
        category.name = name
        category.description = description
        category.save()
        messages.success(request, "Category updated successfully.")
        return redirect('categories')

    # Render the edit category form
    return render(request, 'admin/edit_categories.html', {'category': category})

def delete_category(request, category_id):
    # Get the category object or return 404 if it doesn't exist
    category = get_object_or_404(Category, id=category_id)

    # Delete the category
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('categories')


def create_referral_offer(request):
    if request.method == 'POST':
        try:
            ReferralOffer.objects.create(
                offer_name=request.POST.get('offer_name'),
                description=request.POST.get('description'),
                referrer_reward=request.POST.get('referrer_reward'),
                referred_reward=request.POST.get('referred_reward'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                is_active=request.POST.get('is_active') == 'on'
            )
            messages.success(request, 'Referral offer created successfully!')
            return redirect('offers')
        except Exception as e:
            messages.error(request, f'Error creating offer: {str(e)}')
    
    return render(request, 'admin/offers/create_referral_offer.html')


def create_referral_offer(request):
    if request.method == 'POST':
        try:
            ReferralOffer.objects.create(
                offer_name=request.POST.get('offer_name'),
                description=request.POST.get('description'),
                referrer_reward=request.POST.get('referrer_reward'),
                referred_reward=request.POST.get('referred_reward'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date') or None,
                is_active=request.POST.get('is_active') == 'on'
            )
            messages.success(request, 'Referral offer created successfully!')
            return redirect('offer_list')
        except Exception as e:
            messages.error(request, f'Error creating offer: {str(e)}')
    return render(request, 'admin/offers/create_referral_offer.html')

def edit_referral_offer(request, offer_id):
    referral_offer = get_object_or_404(ReferralOffer, id=offer_id)
    if request.method == 'POST':
        try:
            referral_offer.offer_name = request.POST.get('offer_name')
            referral_offer.description = request.POST.get('description')
            referral_offer.referrer_reward = request.POST.get('referrer_reward')
            referral_offer.referred_reward = request.POST.get('referred_reward')
            referral_offer.start_date = request.POST.get('start_date')
            referral_offer.end_date = request.POST.get('end_date') or None
            referral_offer.is_active = request.POST.get('is_active') == 'on'
            referral_offer.save()
            messages.success(request, 'Referral offer updated successfully!')
            return redirect('offers')
        except Exception as e:
            messages.error(request, f'Error updating offer: {str(e)}')
    return render(request, 'admin/offers/edit_referral_offer.html', {'offer': referral_offer})

def toggle_referral_offer(request, offer_id):
    referral_offer = get_object_or_404(ReferralOffer, id=offer_id)
    referral_offer.is_active = not referral_offer.is_active
    referral_offer.save()
    action = "activated" if referral_offer.is_active else "deactivated"
    messages.success(request, f'Offer {action} successfully!')
    return redirect('offers')

def delete_referral_offer(request, offer_id):
    referral_offer = get_object_or_404(ReferralOffer, id=offer_id)
    referral_offer.delete()
    messages.success(request, 'Offer deleted successfully!')
    return redirect('offer_list')


def export_orders_excel(request):
    start_date = request.GET.get("startDate")
    end_date = request.GET.get("endDate")
    predefined_range = request.GET.get("predefinedRange")

    if start_date:
        start_date = parse_date(start_date)
    if end_date:
        end_date = parse_date(end_date)

    today = date.today()
    if predefined_range:
        if predefined_range == "oneDay":
            start_date, end_date = today - timedelta(days=1), today
        elif predefined_range == "oneWeek":
            start_date, end_date = today - timedelta(weeks=1), today
        elif predefined_range == "oneMonth":
            start_date, end_date = today - timedelta(days=30), today
        elif predefined_range == "oneYear":
            start_date, end_date = today - timedelta(days=365), today

    orders = Order.objects.all()
    if start_date and end_date:
        orders = orders.filter(created_at__range=[start_date, end_date])

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Sales Report')

    # Define headers
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Order ID', 'Customer', 'Date', 'Total Price', 'Total Discount', 'Payment Status']

    for col_num, column_title in enumerate(columns):
        ws.write(row_num, col_num, column_title, font_style)

    # Fetch filtered order data
    font_style = xlwt.XFStyle()
    orders = orders.values_list('id', 'customer__username', 'created_at', 'total_price', 'total_discount', 'payment_status')

    for order in orders:
        row_num += 1
        for col_num, cell_value in enumerate(order):
            ws.write(row_num, col_num, str(cell_value), font_style)

    wb.save(response)
    return response


def export_orders_pdf(request):
    start_date = request.GET.get("startDate")
    end_date = request.GET.get("endDate")
    predefined_range = request.GET.get("predefinedRange")

    if start_date:
        start_date = parse_date(start_date)
    if end_date:
        end_date = parse_date(end_date)

    today = date.today()
    if predefined_range:
        if predefined_range == "oneDay":
            start_date, end_date = today - timedelta(days=1), today
        elif predefined_range == "oneWeek":
            start_date, end_date = today - timedelta(weeks=1), today
        elif predefined_range == "oneMonth":
            start_date, end_date = today - timedelta(days=30), today
        elif predefined_range == "oneYear":
            start_date, end_date = today - timedelta(days=365), today

    orders = Order.objects.all()
    if start_date and end_date:
        orders = orders.filter(created_at__range=[start_date, end_date])

    html_string = render_to_string('admin/orders_pdf_template.html', {'orders': orders})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    temp_file_path = os.path.join(tempfile.gettempdir(), "sales_report.pdf")

    try:
        HTML(string=html_string).write_pdf(temp_file_path)
        
        with open(temp_file_path, 'rb') as pdf_file:
            response.write(pdf_file.read())

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return response

def bestselling(request):
    # Best selling products (considering only completed orders)
    top_products = Product.objects.filter(
        order_items__order__status__in=['delivered', 'shipped']
    ).annotate(
        total_sold=Sum('order_items__quantity'),
        total_revenue=Sum(F('order_items__quantity') * F('order_items__price'))
    ).order_by('-total_sold')[:10]

    # Top selling categories
    top_categories = Category.objects.annotate(
        total_sold=Sum(
            'product__order_items__quantity',
            filter=Q(product__order_items__order__status__in=['delivered', 'shipped'])
        ),
        total_revenue=Sum(
            F('product__order_items__quantity') * F('product__order_items__price'),
            filter=Q(product__order_items__order__status__in=['delivered', 'shipped'])
        )
    ).exclude(total_sold=None).order_by('-total_revenue')[:5]

    context = {
        'top_products': top_products,
        'top_categories': top_categories,
    }
    return render(request, 'admin/bestselling/bestselling.html', context)

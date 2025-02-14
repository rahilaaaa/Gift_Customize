from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.http import JsonResponse
from users.models import Address
from products.models import Product, ProductVariant, ProductCustomization, Coupon, CouponUsage, ProductImage, Category
from .models import Cart, CartItem, Order, OrderItem,Wishlist,WishlistItem
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.views.decorators.cache import never_cache
from decimal import Decimal
from django.core.files.images import get_image_dimensions
from PIL import Image
from io import BytesIO
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from django.db.models import Min

# # Function to check if a user is a superuser
# def is_superuser(user):
#     return user.is_superuser

# @never_cache
# @user_passes_test(is_superuser, login_url='login')
# def add_products(request):
#     if request.method == 'POST':
#         # Retrieve form data
#         title = request.POST.get('title')
#         priority = request.POST.get('priority')
#         description = request.POST.get('description')
#         price = request.POST.get('price')
#         category_name = request.POST.get('product_category')

#         # Validate required fields
#         required_fields = {
#             'Title': title,
#             'Priority': priority,
#             'Description': description,
#             'Price': price,
#             'Product Category': category_name,
#         }

#         missing_fields = [field for field, value in required_fields.items() if not value]
#         if (missing_fields):
#             for field in missing_fields:
#                 messages.error(request, f"{field} is required.")
#             return redirect('add_products')

#         # Validate price is a positive integer
#         try:
#             price = int(price)
#             if price <= 0:
#                 raise ValueError("Price must be a positive integer.")
#         except ValueError as e:
#             messages.error(request, f"Invalid price: {str(e)}")
#             return redirect('add_products')

#         # Validate at least 3 images are uploaded
#         images = [request.FILES.get(f'image{i}') for i in range(1, 4)]
#         if not all(images):
#             messages.error(request, "Please upload exactly 3 images.")
#             return redirect('add_products')

#         # Validate image dimensions and resize if necessary
#         for image in images:
#             try:
#                 img = Image.open(image)
#                 width, height = img.size
#                 if width > 800 or height > 800:  # Resize if dimensions exceed 800x800
#                     img.thumbnail((800, 800))
#                     buffer = BytesIO()
#                     img.save(buffer, format='JPEG')
#                     image.file = buffer
#             except Exception as e:
#                 messages.error(request, f"Invalid image file: {str(e)}")
#                 return redirect('add_products')

#         # Get the Category instance
#         try:
#             category = Category.objects.get(name=category_name)
#         except Category.DoesNotExist:
#             messages.error(request, f"Category '{category_name}' not found.")
#             return redirect('add_products')

#         # Create and save the Product instance
#         try:
#             product = Product(
#                 title=title,
#                 description=description,
#                 priority=priority,
#                 price=price,
#                 category=category,
#             )
#             product.save()
#         except Exception as e:
#             messages.error(request, f"Error saving product: {str(e)}")
#             return redirect('add_products')

#         # Save images
#         for i, image in enumerate(images, start=1):
#             try:
#                 product_image = ProductImage(product=product, image=image)
#                 product_image.save()
#             except Exception as e:
#                 messages.error(request, f"Error saving image {i}: {str(e)}")
#                 return redirect('add_products')

#         # Save variants with size, color, liter, charm, charmImg, and viewflex
#         for i in range(1, 4):  # Assuming a maximum of 3 variants
#             color = request.POST.get(f'color{i}')
#             size = request.POST.get(f'size{i}')
#             liter = request.POST.get(f'liter{i}')
#             quantity = request.POST.get(f'quantity{i}')
#             charm = request.POST.get(f'charm{i}')
#             charmImg = request.FILES.get(f'charmImg{i}')
#             viewflex = request.POST.get(f'viewflex{i}')
#             print(f"Variant {i} - Viewflex: {viewflex}")  # Debugging line

#             if (color or size or liter) and quantity:
#                 try:
#                     quantity = int(quantity)
#                     if quantity < 0:
#                         raise ValueError("Quantity must be a non-negative integer.")
#                     variant = ProductVariant(
#                         product=product,
#                         color=color,
#                         size=size,
#                         liter=liter,
#                         quantity=quantity,
#                         charm=charm,
#                         charmImg=charmImg,
#                         viewflex=viewflex
#                     )
#                     variant.save()
#                 except ValueError as ve:
#                     messages.error(request, f"Invalid quantity for variant {i}: {str(ve)}")
#                 except Exception as e:
#                     messages.error(request, f"Error saving variant {i}: {str(e)}")

#         messages.success(request, "Product added successfully.")
#         return redirect('add_products')

#     return render(request, 'admin/product/add_products.html')


def add_to_cart(request):
    if request.method == "POST":
        print(request.POST)  # Debugging: Print all POST data

        # Retrieve product_id and category-specific variant
        product_id = request.POST.get('product_id')

        # Fetch the product
        product = get_object_or_404(Product, id=product_id)
        category_name = product.category.name.lower()  # Get category name from the product

        # Initialize variant and variant filters
        variant = None
        variant_filters = {'product': product}

        # Handle variants based on category
        if category_name == 'wallet':
            color = request.POST.get('color')
            charm = request.POST.get('charm')
            charm_img = request.FILES.get('charmImg')
            customization_text = request.POST.get('wallet-name', '').strip()  # Retrieve customization text for wallet

            if color:
                variant_filters['color'] = color
            if charm:
                variant_filters['charm'] = charm
            if charm_img:
                variant_filters['charm_img'] = charm_img
        elif category_name == '3d_crystal':
            size = request.POST.get('size')
            view_flex = request.POST.get('view-type')

            if size:
                variant_filters['size'] = size
            if view_flex:
                variant_filters['viewflex'] = view_flex
        elif category_name == 'water_bottle':
            liter = request.POST.get('liter')
            customization_text = request.POST.get('wallet-name', '').strip()  # Retrieve customization text for wallet

            if liter:
                variant_filters['liter'] = liter

        # Retrieve the variant if filters are applied
        if variant_filters:
            variant = ProductVariant.objects.filter(**variant_filters).first()
            if not variant:
                return JsonResponse({'error': 'Selected variant is not available.'}, status=404)

        # Validate and process the quantity
        quantity = request.POST.get('quantity', '').strip()
        if not quantity.isdigit() or int(quantity) <= 0:
            return JsonResponse({'error': 'Invalid quantity provided.'}, status=400)
        quantity = int(quantity)

        # Check if the requested quantity exceeds the available stock
        if quantity > variant.quantity:
            return JsonResponse({'error': 'Requested quantity exceeds available stock.'}, status=400)

        # Handle uploaded image (if any)
        uploaded_image = request.FILES.get('image')

        # Check user authentication and manage the cart
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(customer=request.user)
            cart_item = CartItem.objects.filter(cart=cart, product=product, variant=variant).first()

            if cart_item:
                if cart_item.quantity + quantity > variant.quantity:
                    return JsonResponse({'error': 'Requested quantity exceeds available stock.'}, status=400)
                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                    price=product.price
                )

            # Handle image and text customization (if applicable)
            customization_data = {}
            if uploaded_image:
                image_path = default_storage.save(f"customizations/{uploaded_image.name}", uploaded_image)
                customization_data['customization_image'] = image_path
            if category_name == 'wallet' or category_name == 'water_bottle' and customization_text:
                customization_data['customization_text'] = customization_text

            # In add_to_cart view, after creating ProductCustomization:
            if customization_data:
                customization = ProductCustomization.objects.create(
                    product=product,
                    customer=request.user,
                    **customization_data
                )
                # Link to cart item
                cart_item.customization = customization
                cart_item.save()

            return redirect('cart')  # Redirect to the cart page after successful addition

        else:
            # Redirect to login page if user is not authenticated
            return redirect('login_user')

    # Handle invalid request methods
    return JsonResponse({'error': 'Invalid request method. Only POST requests are allowed.'}, status=400)


def update_cart_quantity(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            new_quantity = int(data.get('quantity'))

            if new_quantity <= 0:
                return JsonResponse({'error': 'Quantity must be greater than zero.'}, status=400)

            cart_item = CartItem.objects.get(id=item_id, cart__customer=request.user)
            if new_quantity > cart_item.variant.quantity:
                return JsonResponse({'error': 'Requested quantity exceeds available stock.'}, status=400)

            cart_item.quantity = new_quantity
            cart_item.save()

            # Calculate updated totals
            cart = cart_item.cart
            subtotal = sum(item.quantity * item.price for item in cart.items.all())
            total = subtotal + 10  # Add shipping cost

            return JsonResponse({'success': True, 'subtotal': float(subtotal), 'total': float(total)})

        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f"An unexpected error occurred: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def remove_from_cart(request, cart_item_id):
    item = get_object_or_404(CartItem, id=cart_item_id)
    cart = item.cart  # Assuming the item is linked to a cart
    item.delete()  # Remove the item from the cart
    cart.save()  # Save the cart if necessary
    return redirect('cart')  # Redirect to the cart page


def cart(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(customer=request.user)
            cart_items = CartItem.objects.filter(cart=cart).select_related('customization')
        except Cart.DoesNotExist:
            cart_items = []

        # Ensure subtotal and shipping_cost are Decimal
        subtotal = sum(Decimal(item.quantity) * item.price for item in cart_items)
        shipping_cost = Decimal('10.00')

        # Convert discount_amount from float to Decimal
        discount_amount = Decimal(request.session.get('coupon_discount', 0))
        total = max(Decimal('0.00'), subtotal - discount_amount + shipping_cost)

        # Calculate cart count
        cart_count = cart.items.count() if cart else 0

        # Fetch the minimum purchase amount from the database
        minimum_purchase_amount = Coupon.objects.filter(active=True).aggregate(Min('minimum_purchase'))['minimum_purchase__min'] or Decimal('0.00')

        # Check if the subtotal meets the minimum purchase amount
        meets_minimum_purchase = subtotal >= minimum_purchase_amount
    
      # Calculate wishlist count
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0

        # Fetch active coupons if the subtotal exceeds the minimum purchase amount
        active_coupons = []
        if meets_minimum_purchase:
            active_coupons = Coupon.objects.filter(active=True, valid_from__lte=datetime.now(), valid_to__gte=datetime.now())

        return render(request, 'orders/cart/cart.html', {
            'cart_items': cart_items,
            'total': total,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'discount_amount': discount_amount,
            'cart_count': cart_count,  # Add cart count to context
            'active_coupons': active_coupons,  # Add active coupons to context
            'wishlist_count': wishlist_count,  # Add wishlist count to context
            'meets_minimum_purchase': meets_minimum_purchase,  # Add minimum purchase status to context
        })
    return redirect('user_login')


def cart_details(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=request.user)
    cart_items = [cart_item]  # Convert it to a list to match the template structure
    
    print(f"Product: {cart_item.product}, Quantity: {cart_item.quantity}, Category: {cart_item.product.category.name}")

    return render(request, 'orders/cart/cart_details.html', {
        'cart_items': cart_items,
    })


def apply_coupon(request):
    code = request.POST.get('coupon_code')

    try:
        # Fetch the user's cart
        cart = request.user.cart  # This uses the related_name "cart" from the Cart model
        cart_items = cart.items.all()
        
        # Calculate subtotal
        subtotal = sum(item.get_total_price() for item in cart_items)

        # Fetch the coupon
        coupon = Coupon.objects.get(code=code, active=True)

        # Check if the user has already used this coupon
        if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
            messages.error(request, "You have already used this coupon.")
            return redirect('cart')

        # Apply the discount
        discount_amount = coupon.apply_discount(subtotal)
        discounted_total = max(Decimal('0.00'), subtotal - discount_amount)

        # Increment coupon usage
        coupon.total_uses += 1
        coupon.save()

        # Store the discount in session as a float
        request.session['coupon_discount'] = float(discount_amount)
        request.session['coupon_id'] = coupon.id  # Save coupon ID in session

        # Set the coupon for each cart item
        for item in cart_items:
            item.coupon = coupon
            item.save()


        # Record the coupon usage
        CouponUsage.objects.create(user=request.user, coupon=coupon)

        messages.success(request, f"Coupon applied! You saved ${discount_amount:.2f}.")
        return redirect('cart')

    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon code.")
        return redirect('cart')

    except Cart.DoesNotExist:
        messages.error(request, "No cart found.")
        return redirect('cart')


def checkout(request):
    try:
        cart = Cart.objects.get(customer=request.user)
        cart_items = cart.items.all()  # Get related CartItems
        total_amount = sum(item.get_total_price() for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total_amount = 0

    # Ensure subtotal and shipping_cost are Decimal
    subtotal = sum(Decimal(item.quantity) * item.price for item in cart_items)
    shipping_cost = Decimal('10.00')

    # Convert discount_amount from float to Decimal
    discount_amount = Decimal(request.session.get('coupon_discount', 0))
    total = max(Decimal('0.00'), subtotal - discount_amount + shipping_cost)

    # Fetch user addresses dynamically
    user_addresses = Address.objects.filter(user=request.user)
    if request.user.is_authenticated:
        cart = Cart.objects.filter(customer=request.user).first()
        cart_count = cart.items.count() if cart else 0
    else:
        cart_count = 0

    return render(request, 'orders/checkout/checkout.html', {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'total': total,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'user_addresses': user_addresses,  # Pass addresses to template
        'cart_count': cart_count,  # Add cart count to context

    })


@login_required
def place_order(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Fetch the user's cart
                cart = Cart.objects.get(customer=request.user)
                cart_items = cart.items.all()

                # Calculate subtotal
                subtotal = sum(item.get_total_price() for item in cart_items)
                shipping_cost = Decimal('10.00')
                discount_amount = Decimal(request.session.get('coupon_discount', 0))
                total = max(Decimal('0.00'), subtotal - discount_amount + shipping_cost)

                # Fetch addresses
                address_id = request.POST.get('address')
                address = get_object_or_404(Address, id=address_id, user=request.user)
                payment_method = request.POST.get('payment_method')
                payment_status = 'Pending'

                # Create the order
                order = Order.objects.create(
                    customer=request.user,
                    status=Order.PENDING,
                    total_price=total,
                    shipping_address=address.full_address(),
                    billing_address=address.full_address(),
                    payment_method=payment_method,
                    shipping_cost=shipping_cost,
                    payment_status=payment_status
                )

                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=item.price,
                        customization=item.customization,
                        coupon=item.coupon  # Add coupon to OrderItem

                    )

                # Clear the cart
                cart.items.all().delete()

                # Clear the coupon discount from session
                if 'coupon_discount' in request.session:
                    del request.session['coupon_discount']

                messages.success(request, "Order placed successfully!")
                return redirect('order_confirmation', order_id=order.id)

        except Exception as e:
            messages.error(request, f"An error occurred while placing the order: {str(e)}")
            return redirect('checkout')

    return redirect('checkout')


@login_required
def order_confirmation(request, order_id):
        # Calculate cart count
    if request.user.is_authenticated:
        cart = Cart.objects.filter(customer=request.user).first()
        cart_count = cart.items.count() if cart else 0
    else:
        cart_count = 0
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order, 'cart_count': cart_count})

@login_required
def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = wishlist.items.all()
    
    # Calculate wishlist count
    wishlist_count = wishlist_items.count()
    
    # Calculate cart count
    cart = Cart.objects.filter(customer=request.user).first()
    cart_count = cart.items.count() if cart else 0

    return render(request, 'orders/whishlist/whishlist.html', {
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_count,  # Add wishlist count to context
        'cart_count': cart_count,  # Add cart count to context
    })


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    if created:
        messages.success(request, f"{product.title} has been added to your wishlist.")
    else:
        messages.info(request, f"{product.title} is already in your wishlist.")
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist_item = get_object_or_404(WishlistItem, wishlist=wishlist, product=product)
    wishlist_item.delete()
    messages.success(request, f"{product.title} has been removed from your wishlist.")
    return redirect('wishlist')



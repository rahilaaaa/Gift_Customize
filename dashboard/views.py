from django.shortcuts import render, redirect,get_object_or_404
from products.models import Product, ProductVariant, ProductImage,Review,Coupon
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout
from datetime import datetime
from django.contrib.auth import get_user_model
from django.views.decorators.cache import never_cache
from products.models import Category,Offer
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.images import get_image_dimensions
from PIL import Image
from io import BytesIO
from django.db import transaction
from .forms import CouponForm
from decimal import Decimal, InvalidOperation
from django.contrib.contenttypes.models import ContentType



# Function to check if a user is a superuser
def is_superuser(user):
    return user.is_superuser


@never_cache
def login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('dashboard')  # Redirect superusers to the admin pag
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return render(request, 'admin/login.html', {'error': 'Email and password are required.'})

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_superuser:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'admin/login.html', {'error': 'Access restricted to superusers.'})
        else:
            return render(request, 'admin/login.html', {'error': 'Invalid email or password. Please try again.'})

    return render(request, 'admin/login.html')


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def admin(request):
    print(f"User: {request.user}, Authenticated: {request.user.is_authenticated}, Superuser: {request.user.is_superuser}")
    return render(request, 'admin/index.html')
    
@never_cache
def logout_view(request):
    logout(request)
    return redirect('login')

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
    products = Product.objects.prefetch_related('images')
    
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
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validate required fields
                required_fields = {
                    'title': request.POST.get('title'),
                    'priority': request.POST.get('priority'),
                    'description': request.POST.get('description'),
                    'price': request.POST.get('price'),
                }

                # Check for missing required fields
                missing_fields = [field for field, value in required_fields.items() if not value]
                if missing_fields:
                    for field in missing_fields:
                        messages.error(request, f"{field.title()} is required and cannot be empty.")
                    return redirect('edit_product', product_id=product_id)

                # Validate price is a positive integer
                try:
                    price = float(required_fields['price'])
                    if price < 0:
                        messages.error(request, "Price must be a positive integer.")
                        return redirect('edit_product', product_id=product_id)
                except ValueError:
                    messages.error(request, "Price must be a valid integer.")
                    return redirect('edit_product', product_id=product_id)

                # Update product fields
                product.title = required_fields['title']
                product.priority = required_fields['priority']
                product.description = required_fields['description']
                product.price = price  # Use the validated price
                product.save()

                # Handle image updates
                for i in range(1, 4):
                    image = request.FILES.get(f'image{i}')
                    if image:
                        # Validate image file type
                        if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                            messages.error(request, "Invalid image format. Only PNG, JPG, and JPEG are allowed.")
                            return redirect('edit_product', product_id=product_id)

                        # Update or create images
                        try:
                            product_image = product.images.all()[i-1]  # Get existing image by index
                            product_image.image.delete(save=False)  # Delete old file
                            product_image.image = image
                            product_image.save()
                        except IndexError:
                            ProductImage.objects.create(product=product, image=image)

                # Handle variants
                variants = list(product.variants.all())
                
                for i in range(1, 4):
                    color = request.POST.get(f'color{i}')
                    size = request.POST.get(f'size{i}')
                    liter = request.POST.get(f'liter{i}')
                    quantity = request.POST.get(f'quantity{i}')
                    charm = request.POST.get(f'charm{i}')
                    charm_img = request.FILES.get(f'charmImg{i}')
                    view_flex = request.POST.get(f'viewFlex{i}')

                    # Check if variant fields are required based on category
                    if product.category.name.lower() == "wallet":
                        if not color:
                            messages.error(request, f"Color for variant {i} is required and cannot be empty.")
                            return redirect('edit_product', product_id=product_id)
                    elif product.category.name.lower() == "3d_crystal":
                        if not size:
                            messages.error(request, f"Size for variant {i} is required and cannot be empty.")
                            return redirect('edit_product', product_id=product_id)

                    # Only process variants with valid data
                    if any([color, size, liter, charm, charm_img, view_flex]) and quantity:
                        try:
                            # Get existing variant or create new
                            variant = variants[i-1] if i-1 < len(variants) else ProductVariant(product=product)
                            
                            # Validate quantity
                            try:
                                variant.quantity = int(quantity)
                            except ValueError:
                                messages.error(request, f"Quantity for variant {i} must be a valid number.")
                                return redirect('edit_product', product_id=product_id)

                            # Update fields based on category
                            if product.category.name.lower() == "wallet":
                                variant.color = color or None
                                variant.size = None
                                variant.liter = None
                                variant.charm = charm or None
                                variant.charm_img = charm_img or None
                            elif product.category.name.lower() == "3d_crystal":
                                variant.size = size or None
                                variant.color = None
                                variant.liter = None
                                variant.view_flex = view_flex or None

                            # Update additional fields

                            

                            variant.save()
                        except Exception as e:
                            messages.error(request, f"Error saving variant {i}: {str(e)}")
                            return redirect('edit_product', product_id=product_id)

                messages.success(request, "Product updated successfully.")
                return redirect('products')

        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
            return redirect('edit_product', product_id=product_id)

    # Filter variants based on category
    variants = product.variants.all()
    context = {
        'product': product,
        'images': product.images.all(),
        'variants': variants,
        'category': product.category,
    }
    return render(request, 'admin/product/edit_product.html', context)


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, f"Product '{product.title}' has been deleted successfully.")
    return redirect('products')  # Redirect to the product list page


@user_passes_test(is_superuser, login_url='login')
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

    return render(request, 'admin/orders/orders_list.html')


def order_details(request):
    return render(request, 'admin/orders/order-details.html')

@never_cache
def coupon(request):
    coupons = Coupon.objects.all().order_by('-valid_from')  # Fetch all coupons, ordered by validity
    return render(request, 'admin/coupon/coupon.html', {'coupons': coupons})

@never_cache
def create_coupon(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.save()  # Save first to get ID

            # Add M2M relationships
            coupon.products.set(request.POST.getlist('products'))
            coupon.categories.set(request.POST.getlist('categories'))

            messages.success(request, 'Coupon created successfully!')
            return redirect('create_coupon')
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
    coupon.delete()
    messages.success(request, 'Coupon deleted successfully!')
    return redirect('coupon')

def offer(request):
    # Fetch all offers and optimize queries using select_related and prefetch_related
    offers = Offer.objects.select_related('content_type').all()

    # Render the offers.html template and pass the offers as context
    context = {
        'offers': offers
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
                if not (0 < percentage <= 100):
                    errors['percentage'] = 'Percentage must be between 0.01 and 100'
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
                if offer_percentage <= 0 or offer_percentage > 100:
                    errors['percentage'] = 'Percentage must be between 0 and 100'
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
                if not (0 < percentage <= 100):
                    errors['percentage'] = 'Percentage must be between 0.01 and 100'
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
        name = request.POST.get('name', '').strip()
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

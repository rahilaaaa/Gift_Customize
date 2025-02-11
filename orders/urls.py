from django.urls import path
from . import views

urlpatterns = [
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart, name="cart"),
    path('cart_details/<int:item_id>/', views.cart_details, name='cart_details'),
    path("update-cart-quantity/", views.update_cart_quantity, name="update_cart_quantity"),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/', views.checkout, name='checkout'),



]

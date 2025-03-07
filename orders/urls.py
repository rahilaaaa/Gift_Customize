from django.urls import path
from . import views

urlpatterns = [
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart, name="cart"),
    path('cart_details/<int:item_id>/', views.cart_details, name='cart_details'),
    path('update_cart_quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/', views.checkout, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),
    path('check-wallet-balance/', views.check_wallet_balance, name='check_wallet_balance'),
    path('payment-failed/<int:order_id>/', views.payment_failed, name='payment_failed'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path("paypal-payment/", views.paypal_payment, name="paypal_payment"),
    path("paypal-success/", views.paypal_success, name="paypal_success"),
    path("paypal-cancel/", views.paypal_cancel, name="paypal_cancel"),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    # path('verify-payment/', views.verify_payment, name='verify_payment'),
    

]

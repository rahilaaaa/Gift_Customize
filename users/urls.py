from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('otp_verification/', views.otp_verification, name='otp_verification'),
    path('login/',views.login_view,name='login_user'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('profile/',views.profile, name='profile'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),

    path('reset_password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('logout/',views.logout_view, name='logout'),
    path('add-address/', views.add_new_address, name='add_address'),
    path('edit_address/<int:pk>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:pk>/', views.delete_address, name='delete_address'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # path('my_orders/', views.my_orders, name='my_orders'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),  # Add this line for order detail view

    path('change_password/', views.change_password, name='change_password'),
    path('edit_account/<int:user_id>/', views.edit_account, name='edit_account'),
   



   
]

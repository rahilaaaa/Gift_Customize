from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('otp_verification/', views.otp_verification, name='otp_verification'),
    path('login/',views.login_view,name='login_user'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('contact/',views.contact,name='contact'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('profile/',views.profile, name='profile'),
    path('reset_password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('logout/',views.logout_view, name='logout'),
    path('add-address/', views.add_new_address, name='add_address'),
    path('edit_address/<int:pk>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:pk>/', views.delete_address, name='delete_address')

   



   
]

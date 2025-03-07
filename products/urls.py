from django.urls import path
from . import views


urlpatterns = [
    path('',views.home,name='home'),
    path('shop/',views.shop,name='shop'),
    path('product/<pk>/', views.product_details, name='product_details'),
    path('submit-review/<int:pk>/', views.submit_review, name='submit_review'),
    # path('upload-image/<int:product_id>/', views.upload_image, name='upload_image'),
   
    
  

 


]




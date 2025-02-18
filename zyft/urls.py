from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('users/',include('users.urls')),
    path('',include('products.urls')),
    path('admin/',include('dashboard.urls')),
    path('accounts/', include('allauth.urls')),
    path('orders/',include('orders.urls')),
    path('chatbot/',include('chatbot.urls')),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

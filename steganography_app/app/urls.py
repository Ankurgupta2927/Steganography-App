from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('encode/', views.encode_message, name='encode'),
    path('decode/', views.decode_message, name='decode'),
    path('download/<str:filename>/', views.download_image, name='download'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
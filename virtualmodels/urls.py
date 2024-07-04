from django.contrib import admin
from django.urls import path

from main.views import TestDetailView, TestView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', TestView.as_view(), name='test_view'),
    path('<int:pk>/', TestDetailView.as_view(), name='thing_detail'),
]

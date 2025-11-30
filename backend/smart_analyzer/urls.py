"""
URL configuration for smart_analyzer project.
"""
from django.urls import path, include

urlpatterns = [
    path('api/', include('tasks.urls')),
]


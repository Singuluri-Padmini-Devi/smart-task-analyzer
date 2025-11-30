"""
URL routing for tasks API.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('tasks/analyze/', views.analyze_tasks_view, name='analyze_tasks'),
    path('tasks/suggest/', views.suggest_tasks_view, name='suggest_tasks'),
    path('strategies/', views.strategies_view, name='strategies'),
]


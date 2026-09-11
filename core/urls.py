from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('google-calendar/connect/', views.google_calendar_connect, name='google-calendar-connect'),
    path('google-calendar/callback/', views.google_calendar_callback, name='google-calendar-callback'),
]

# apps/debugger/urls.py
from django.urls import path
from . import views

app_name = 'debugger'

urlpatterns = [
    path('', views.debug_assistant, name='debug_assistant'),
    path('submit/', views.submit_debug_query, name='submit_query'),
]


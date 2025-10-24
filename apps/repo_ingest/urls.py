# apps/repo_ingest/urls.py
from django.urls import path
from . import views

app_name = 'repo_ingest'

urlpatterns = [
    # Repository list
    path('', views.repository_list, name='repository_list'),
    
    # Upload
    path('upload/', views.repository_upload_page, name='upload_page'),
    path('upload/submit/', views.repository_upload, name='upload_submit'),
    
    # Status & monitoring
    path('<uuid:repo_id>/status/', views.repository_status, name='repository_status'),
    path('<uuid:repo_id>/status/api/', views.repository_status_api, name='repository_status_api'),
    
    # GitHub sync
    path('<uuid:repo_id>/sync/', views.repository_sync, name='repository_sync'),
    
    # Delete
    path('<uuid:repo_id>/delete/', views.repository_delete, name='repository_delete'),
]


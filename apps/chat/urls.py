from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_session_list, name='session_list'),
    path('new/', views.chat_session_create, name='session_create'),
    path('<int:session_id>/', views.chat_session_detail, name='session_detail'),
    path('<int:session_id>/stream/', views.chat_message_stream, name='message_stream'),
    path('<int:session_id>/message/', views.chat_message_create, name='message_create'),
    path('<int:session_id>/delete/', views.chat_session_delete, name='session_delete'),
    path('<int:session_id>/rename/', views.chat_session_rename, name='session_rename'),
    path('memory/stats/', views.memory_stats, name='memory_stats'),
    path('memory/debug/', views.memory_debug, name='memory_debug'),
    

]

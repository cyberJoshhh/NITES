from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('diagnostics/', views.diagnostics, name='diagnostics'),
    path('api/messages/<str:room_name>/', views.message_api, name='message_api'),
    path('api/server-info/', views.server_info_api, name='server_info_api'),
    path('<str:room_name>/', views.room, name='room'),
] 
from django.urls import path
from . import views

urlpatterns = [
    path('', views.message_home, name='message_home'),
    path('get_messages/', views.get_messages, name='get_messages'),
    path('get_group_messages/', views.get_group_messages, name='get_group_messages'),
    path('send_message/', views.send_message, name='send_message'),
    path('create_group/', views.create_group, name='create_group'),
    path('get_unread_count/', views.get_unread_count, name='get_unread_count'),
    
    # Dedicated URL pattern for group members
    path('group/<int:group_id>/members/', views.get_group_members_fixed, name='get_group_members_fixed'),
    
    # HTML view for group members (directly rendered)
    path('group/<int:group_id>/members/view/', views.group_members_view, name='group_members_view'),
    
    # Keep original for compatibility
    path('get_group_members/', views.get_group_members, name='get_group_members'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
    path('send-message/', views.send_message, name='send_message'),
    path('fetch-messages/<int:user_id>/', views.fetch_messages, name='fetch_messages'),
    path('delete-messages/', views.delete_messages, name='delete_messages'),
]

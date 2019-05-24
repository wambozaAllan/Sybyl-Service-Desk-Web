from django.urls import path
from . import views

urlpatterns = [
    path('directMessages', views.direct_message_pane, name='directMessages'),
    path('clientChat/', views.search_company_chat_users, name='searchChatClient'),
    path('directChat/', views.direct_message_chat_room, name='sendUserChatMessage'),
    path('deleteDirectMessage/', views.delete_direct_msg, name='deleteDirectChatMessage'),
]

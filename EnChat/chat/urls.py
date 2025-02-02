from django.urls import path
from . import views

urlpatterns = [
    path("", views.conversations, name="conversations"),
    path("chat/<int:receiver_id>/", views.chat, name="chat"),
    path("send_message/<int:receiver_id>/", views.send_message, name="send_message"),
    path("read_message/<int:message_id>/", views.read_message, name="read_message"),
    path("search/", views.search_user, name="search_user"),
    path(
        "delete_message/<int:message_id>/", views.delete_message, name="delete_message"
    ),
    path("users/", views.get_users, name="users"),
    path("get_messages/<int:receiver_id>/", views.get_messages, name="get_messages"),
]

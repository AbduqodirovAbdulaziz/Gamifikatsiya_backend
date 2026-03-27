from django.contrib import admin
from .models import ChatRoom, Message, MessageReaction


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ["name", "room_type", "classroom", "is_active"]
    list_filter = ["room_type", "is_active"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "room", "content", "created_at"]
    list_filter = ["room", "created_at"]

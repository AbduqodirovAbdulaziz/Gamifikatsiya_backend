from django.contrib import admin
from django.utils.html import format_html

from .models import ChatRoom, Message, MessageReaction


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "type_badge",
        "members_count",
        "active_status",
        "created_at",
    ]
    list_filter = ["room_type", "is_active"]
    readonly_fields = ["created_at"]
    list_per_page = 25

    @admin.display(description="Turi")
    def type_badge(self, obj):
        colors = {
            "classroom": "#6366f1",
            "direct": "#10b981",
            "group": "#f59e0b",
        }
        color = colors.get(obj.room_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            color,
            obj.get_room_type_display(),
        )

    @admin.display(description="A'zolar")
    def members_count(self, obj):
        count = 0
        if obj.classroom_id:
            count = obj.classroom.enrollments.filter(is_active=True).count() + 1
        return format_html(
            '<span style="color:#6366f1;font-weight:700;">{}</span>',
            count,
        )

    @admin.display(description="Holat")
    def active_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">{}</span>',
                "Faol",
            )
        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "Nofaol",
        )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "sender",
        "room",
        "type_badge",
        "short_content",
        "created_at",
    ]
    list_filter = ["message_type", "created_at"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Turi")
    def type_badge(self, obj):
        colors = {
            "text": "#6366f1",
            "image": "#10b981",
            "file": "#f59e0b",
            "voice": "#ef4444",
        }
        color = colors.get(obj.message_type, "#6b7280")
        icon = {
            "text": "chat",
            "image": "image",
            "file": "file",
            "voice": "voice",
        }.get(obj.message_type, "message")
        return format_html(
            '<span style="color:{};font-weight:600;">{} {}</span>',
            color,
            icon,
            obj.message_type.replace("_", " ").title(),
        )

    @admin.display(description="Xabar")
    def short_content(self, obj):
        text = str(obj.content or "")
        return text[:60] + "..." if len(text) > 60 else text or "-"


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "reaction_display", "created_at"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Emoji")
    def reaction_display(self, obj):
        return format_html(
            '<span style="font-size:18px;">{}</span>',
            obj.reaction,
        )

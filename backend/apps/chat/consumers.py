import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import sync_to_async

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "chat_message")
        message = data.get("message", "")
        sender_id = data.get("sender_id")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": message_type,
                "message": message,
                "sender_id": sender_id,
                "channel": self.channel_name,
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                }
            )
        )

    async def typing_indicator(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "sender_id": event["sender_id"],
                    "is_typing": event.get("is_typing", False),
                }
            )
        )


class QuizLiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.quiz_id = self.scope["url_route"]["kwargs"]["quiz_id"]
        self.room_group_name = f"quiz_live_{self.quiz_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type", "score_update")

        await self.channel_layer.group_send(
            self.room_group_name, {"type": event_type, **data}
        )

    async def score_update(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "score_update", "leaderboard": event.get("leaderboard", [])}
            )
        )

    async def question_result(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "question_result",
                    "question_id": event.get("question_id"),
                    "correct_answers": event.get("correct_answers", 0),
                    "total_participants": event.get("total_participants", 0),
                }
            )
        )


class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]
        self.room_group_name = f"tournament_{self.tournament_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "tournament_update", **data}
        )

    async def tournament_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "tournament_update",
                    "standings": event.get("standings", []),
                    "status": event.get("status", ""),
                }
            )
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def notification_message(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "notification", "notification": event.get("notification", {})}
            )
        )

    async def badge_earned(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "badge_earned", "badge": event.get("badge", {})}
            )
        )

    async def level_up(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "level_up",
                    "old_level": event.get("old_level"),
                    "new_level": event.get("new_level"),
                    "title": event.get("title", ""),
                }
            )
        )

    async def challenge_received(self, event):
        await self.send(
            text_data=json.dumps(
                {"type": "challenge_received", "challenge": event.get("challenge", {})}
            )
        )

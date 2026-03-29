import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


class AuthenticatedWebsocketConsumer(AsyncWebsocketConsumer):
    async def authenticate(self, token: str):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return await self.get_user(user_id)
        except (InvalidToken, TokenError, Exception):
            return None

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def get_token_from_query_string(self):
        query_string = self.scope.get("query_string", b"").decode()
        for param in query_string.split("&"):
            if param.startswith("token="):
                return param.split("=")[1]
        return None


class ChatConsumer(AuthenticatedWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = None

        token = self.get_token_from_query_string()
        if not token:
            await self.close()
            return

        self.user = await self.authenticate(token)
        if not self.user:
            await self.close()
            return

        room_valid = await self.verify_room_access()
        if not room_valid:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.broadcast_user_joined()

    async def broadcast_user_joined(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": str(self.user.id),
                "username": self.user.username,
            },
        )

    async def disconnect(self, close_code):
        if self.user:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_left",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                },
            )
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        if not self.user:
            return

        data = json.loads(text_data)
        message_type = data.get("type", "chat_message")

        if message_type == "chat_message":
            message = data.get("message", "")
            if message and message.strip():
                saved_message = await self.save_message(message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "sender_id": str(self.user.id),
                        "sender_username": self.user.username,
                        "message_id": str(saved_message.id) if saved_message else None,
                    },
                )
        elif message_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "sender_id": str(self.user.id),
                    "is_typing": data.get("is_typing", False),
                },
            )

    @database_sync_to_async
    def verify_room_access(self):
        from apps.chat.models import ChatRoom

        try:
            room = ChatRoom.objects.get(id=self.room_id)
            if room.room_type == "classroom":
                from apps.classroom.models import Enrollment

                return (
                    Enrollment.objects.filter(
                        student=self.user, classroom=room.classroom, is_active=True
                    ).exists()
                    or room.classroom.teacher == self.user
                )
            return True
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        from apps.chat.models import ChatRoom, Message

        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return Message.objects.create(
                room=room, sender=self.user, content=content, message_type="text"
            )
        except Exception:
            return None

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "sender_id": event["sender_id"],
                    "sender_username": event.get("sender_username", ""),
                    "message_id": event.get("message_id"),
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

    async def user_joined(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )

    async def user_left(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )


class QuizLiveConsumer(AuthenticatedWebsocketConsumer):
    async def connect(self):
        self.quiz_id = self.scope["url_route"]["kwargs"]["quiz_id"]
        self.room_group_name = f"quiz_live_{self.quiz_id}"
        self.user = None

        token = self.get_token_from_query_string()
        if not token:
            await self.close()
            return

        self.user = await self.authenticate(token)
        if not self.user:
            await self.close()
            return

        is_authorized = await self.verify_quiz_access()
        if not is_authorized:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def verify_quiz_access(self):
        from apps.quizzes.models import Quiz

        try:
            quiz = Quiz.objects.get(id=self.quiz_id)
            if quiz.classroom:
                from apps.classroom.models import Enrollment

                return (
                    Enrollment.objects.filter(
                        student=self.user, classroom=quiz.classroom, is_active=True
                    ).exists()
                    or quiz.created_by == self.user
                )
            return True
        except Quiz.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        if not self.user:
            return

        data = json.loads(text_data)
        event_type = data.get("type", "score_update")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": event_type, "user_id": str(self.user.id), **data},
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


class TournamentConsumer(AuthenticatedWebsocketConsumer):
    async def connect(self):
        self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]
        self.room_group_name = f"tournament_{self.tournament_id}"
        self.user = None

        token = self.get_token_from_query_string()
        if not token:
            await self.close()
            return

        self.user = await self.authenticate(token)
        if not self.user:
            await self.close()
            return

        is_authorized = await self.verify_tournament_access()
        if not is_authorized:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def verify_tournament_access(self):
        from apps.competition.models import Tournament

        try:
            tournament = Tournament.objects.get(id=self.tournament_id)
            if tournament.classroom:
                from apps.classroom.models import Enrollment

                return (
                    Enrollment.objects.filter(
                        student=self.user,
                        classroom=tournament.classroom,
                        is_active=True,
                    ).exists()
                    or tournament.created_by == self.user
                )
            return True
        except Tournament.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        if not self.user:
            return

        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "tournament_update", "user_id": str(self.user.id), **data},
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


class NotificationConsumer(AuthenticatedWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f"user_{self.user_id}"
        self.user = None

        token = self.get_token_from_query_string()
        if not token:
            await self.close()
            return

        self.user = await self.authenticate(token)
        if not self.user or str(self.user.id) != self.user_id:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

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

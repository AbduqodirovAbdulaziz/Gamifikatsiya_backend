import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Notification, PushNotificationLog

User = get_user_model()
logger = logging.getLogger(__name__)


@dataclass
class PushNotificationResult:
    success: bool
    sent_count: int = 0
    failed_count: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class FCMService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if FCMService._initialized:
            return

        self.credentials_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        self.project_id = os.environ.get("FIREBASE_PROJECT_ID")
        self._firebase_app = None
        FCMService._initialized = True

    def _initialize_firebase(self):
        if self._firebase_app is not None:
            return True

        if not self.credentials_path:
            logger.warning("Firebase credentials not configured")
            return False

        try:
            import firebase_admin
            from firebase_admin import credentials

            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_path)
                self._firebase_app = firebase_admin.initialize_app(cred)
            else:
                self._firebase_app = firebase_admin._apps.get("default")

            return True
        except ImportError:
            logger.warning("firebase-admin not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            return False

    def send_to_token(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: int = 1,
        sound: str = "default",
    ) -> bool:
        if not token:
            return False

        if not self._initialize_firebase():
            logger.info(f"FCM not configured, skipping push to token: {token[:20]}...")
            return False

        try:
            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        badge=str(badge),
                        channel_id="edugame_notifications",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            badge=badge,
                            sound=sound,
                        )
                    )
                ),
            )

            response = messaging.send(message)
            logger.info(f"FCM message sent: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send FCM message: {e}")
            return False

    def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not self._initialize_firebase():
            logger.info(f"FCM not configured, skipping push to topic: {topic}")
            return False

        try:
            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f"FCM topic message sent: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send FCM topic message: {e}")
            return False

    def subscribe_to_topic(self, tokens: List[str], topic: str) -> bool:
        if not tokens or not self._initialize_firebase():
            return False

        try:
            from firebase_admin import messaging

            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(f"FCM topic subscription: {response.success_count} success")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to FCM topic: {e}")
            return False

    def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> bool:
        if not tokens or not self._initialize_firebase():
            return False

        try:
            from firebase_admin import messaging

            response = messaging.unsubscribe_from_topic(tokens, topic)
            logger.info(f"FCM topic unsubscription: {response.success_count} success")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from FCM topic: {e}")
            return False


class NotificationService:
    fcm = FCMService()

    @staticmethod
    def create_notification(
        recipient_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        send_push: bool = True,
    ) -> Notification:
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data,
        )

        NotificationService.send_websocket_notification(recipient_id, notification)

        if send_push:
            NotificationService.send_push_notification(notification)

        return notification

    @staticmethod
    def send_push_notification(notification: Notification) -> bool:
        try:
            user = notification.recipient
            fcm_token = getattr(user, "fcm_token", None)

            if not fcm_token:
                PushNotificationLog.objects.create(
                    notification=notification,
                    success=False,
                    error_message="No FCM token",
                )
                return False

            data = notification.data or {}
            data["notification_id"] = str(notification.id)
            data["notification_type"] = notification.notification_type

            success = NotificationService.fcm.send_to_token(
                token=fcm_token,
                title=notification.title,
                body=notification.message,
                data=data,
            )

            PushNotificationLog.objects.create(
                notification=notification,
                success=success,
                error_message="" if success else "Failed to send",
            )

            if success:
                notification.is_sent_push = True
                notification.save(update_fields=["is_sent_push"])

            return success

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            PushNotificationLog.objects.create(
                notification=notification,
                success=False,
                error_message=str(e),
            )
            return False

    @staticmethod
    def send_websocket_notification(user_id: str, notification: Notification):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": "notification_message",
                    "notification": {
                        "id": str(notification.id),
                        "type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "data": notification.data,
                        "created_at": notification.created_at.isoformat(),
                    },
                },
            )
        except Exception as e:
            logger.warning(f"WebSocket notification failed: {e}")

    @staticmethod
    def notify_badge_earned(user_id: str, badge_name: str, badge_icon: str = None):
        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="badge_earned",
            title="Yangi Badge!",
            message=f"Siz '{badge_name}' badgeini oldingiz!",
            data={"badge_name": badge_name, "badge_icon": badge_icon or ""},
        )

    @staticmethod
    def notify_level_up(user_id: str, new_level: int, level_title: str):
        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="level_up",
            title="Level oshdi!",
            message=f"Tabriklaymiz! Siz {new_level}-levelga ko'tarildingiz: {level_title}",
            data={"level": str(new_level), "title": level_title},
        )

    @staticmethod
    def notify_challenge_received(
        challenger_name: str,
        opponent_id: str,
        challenge_id: str,
        quiz_title: str,
    ):
        return NotificationService.create_notification(
            recipient_id=opponent_id,
            notification_type="challenge_received",
            title="Challenge keldi!",
            message=f"{challenger_name} sizga '{quiz_title}' testida challenge yubordi!",
            data={"challenge_id": challenge_id, "quiz_title": quiz_title},
        )

    @staticmethod
    def notify_challenge_result(
        user_id: str,
        result: str,
        opponent_name: str,
        xp_won: int,
        challenge_id: str,
    ):
        if result == "won":
            title = "G'alaba!"
            message = f"Tabriklaymiz! Siz {opponent_name} ustidan g'olib bo'ldingiz! +{xp_won} XP"
        elif result == "lost":
            title = "Yutqazdingiz"
            message = f"{opponent_name} sizni yengdi. Keyingi safar omad tilaymiz!"
        else:
            title = "Challenge yakunlandi"
            message = f"{opponent_name} bilan bellashuv durang bilan yakunlandi."

        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="challenge_result",
            title=title,
            message=message,
            data={"challenge_id": challenge_id, "result": result},
        )

    @staticmethod
    def notify_quiz_result(user_id: str, quiz_title: str, score: float, passed: bool):
        if passed:
            title = "Test muvaffaqiyatli!"
            message = f"Siz '{quiz_title}' testida {score:.0f}% natija ko'rsatdingiz!"
        else:
            title = "Test yakunlandi"
            message = f"Siz '{quiz_title}' testida {score:.0f}% natija ko'rsatdingiz. Qayta urinib ko'ring!"

        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="quiz_result",
            title=title,
            message=message,
            data={"quiz_title": quiz_title, "score": str(score)},
        )

    @staticmethod
    def notify_streak_reminder(user_id: str, current_streak: int):
        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="streak_reminder",
            title="Streak eslatmasi",
            message=f"Sizning streak {current_streak} kun! Bugun dars o'qib streakni saqlang!",
            data={"streak": str(current_streak)},
        )

    @staticmethod
    def notify_daily_quest(user_id: str, quest_type: str, xp_reward: int):
        quest_names = {
            "lesson": "dars o'qish",
            "quiz": "test yechish",
            "social": "do'stga challenge",
            "streak": "kunlik kirish",
        }
        quest_name = quest_names.get(quest_type, quest_type)

        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="daily_quest",
            title="Kunlik vazifa",
            message=f"Bugungi vazifa: {quest_name}! +{xp_reward} XP",
            data={"quest_type": quest_type, "xp_reward": str(xp_reward)},
        )

    @staticmethod
    def notify_tournament_start(
        user_id: str, tournament_title: str, tournament_id: str, start_time: str
    ):
        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="tournament_start",
            title="Turnir boshlanmoqda!",
            message=f"'{tournament_title}' turniri tezlikda boshlanadi!",
            data={
                "tournament_id": tournament_id,
                "start_time": start_time,
            },
        )

    @staticmethod
    def notify_rank_changed(user_id: str, new_rank: int, change: int):
        direction = "yuqoriga" if change > 0 else "pastga"
        return NotificationService.create_notification(
            recipient_id=user_id,
            notification_type="rank_changed",
            title="Reyting o'zgardi",
            message=f"Sizning reytingingiz {direction} ko'tarildi! Hozirgi o'rin: {new_rank}",
            data={"rank": str(new_rank), "change": str(change)},
        )

from rest_framework import serializers
from .models import (
    Badge,
    UserBadge,
    XPTransaction,
    Streak,
    DailyQuest,
    LevelTitle,
    LeaderboardEntry,
)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "badge_type",
            "condition_type",
            "condition_value",
            "xp_bonus",
            "coin_bonus",
            "rarity",
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ["id", "badge", "earned_at", "is_displayed"]


class XPTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XPTransaction
        fields = ["id", "amount", "transaction_type", "description", "created_at"]


class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = [
            "current_streak",
            "longest_streak",
            "last_activity_date",
            "streak_freeze_count",
        ]


class DailyQuestSerializer(serializers.ModelSerializer):
    quest_type_display = serializers.CharField(
        source="get_quest_type_display", read_only=True
    )

    class Meta:
        model = DailyQuest
        fields = [
            "id",
            "quest_type",
            "quest_type_display",
            "target_count",
            "current_count",
            "xp_reward",
            "is_completed",
            "date",
            "completed_at",
        ]


class LevelTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelTitle
        fields = ["level", "title", "min_xp", "max_xp", "icon"]


class GamificationProfileSerializer(serializers.Serializer):
    xp_points = serializers.IntegerField()
    level = serializers.IntegerField()
    level_title = serializers.CharField()
    level_progress = serializers.DictField()
    coins = serializers.IntegerField()
    streak_days = serializers.IntegerField()
    total_quizzes = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    rank_position = serializers.IntegerField(allow_null=True)
    xp_to_next_level = serializers.IntegerField()


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    student = serializers.DictField()
    xp_points = serializers.IntegerField()
    level = serializers.IntegerField()


class LeaderboardSerializer(serializers.Serializer):
    period = serializers.CharField()
    classroom_id = serializers.UUIDField(allow_null=True)
    entries = LeaderboardEntrySerializer(many=True)
    user_rank = serializers.IntegerField(allow_null=True)


class DailyBonusResponseSerializer(serializers.Serializer):
    claimed = serializers.BooleanField()
    xp_earned = serializers.IntegerField(required=False)
    message = serializers.CharField(required=False)


class BadgeEarnedNotificationSerializer(serializers.Serializer):
    badge_id = serializers.UUIDField()
    badge_name = serializers.CharField()
    badge_icon = serializers.CharField(allow_null=True)
    xp_bonus = serializers.IntegerField()
    level_up = serializers.BooleanField()
    new_level = serializers.IntegerField(required=False)

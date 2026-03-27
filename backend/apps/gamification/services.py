import math
from datetime import date, timedelta
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

from .models import (
    Badge,
    UserBadge,
    XPTransaction,
    LeaderboardEntry,
    Streak,
    DailyQuest,
    LevelTitle,
)


class GamificationService:
    @staticmethod
    @transaction.atomic
    def award_xp(user_id, amount, transaction_type, description, related_id=None):
        from apps.users.models import StudentProfile

        try:
            profile = StudentProfile.objects.select_for_update().get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return None

        old_level = profile.level

        profile.xp_points += amount
        profile.total_points_earned += amount
        profile.level = GamificationService.calculate_level(profile.xp_points)
        profile.save()

        XPTransaction.objects.create(
            student_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            related_object_id=related_id,
        )

        GamificationService.update_leaderboard(user_id, amount)

        level_up = profile.level > old_level
        new_badges = []

        if level_up:
            level_title = GamificationService.get_level_title(profile.level)
            GamificationService.check_and_award_badges(
                user_id, "level_up", {"level": profile.level}
            )

        GamificationService.check_and_award_badges(user_id, transaction_type)

        return {
            "xp_earned": amount,
            "total_xp": profile.xp_points,
            "level": profile.level,
            "level_up": level_up,
            "new_badges": new_badges,
        }

    @staticmethod
    def calculate_level(total_xp):
        return math.floor(math.sqrt(total_xp / 100)) + 1

    @staticmethod
    def calculate_xp_for_level(level):
        return (level - 1) ** 2 * 100

    @staticmethod
    def get_xp_progress(total_xp):
        level = GamificationService.calculate_level(total_xp)
        current_level_xp = GamificationService.calculate_xp_for_level(level)
        next_level_xp = GamificationService.calculate_xp_for_level(level + 1)
        xp_in_level = total_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress = (xp_in_level / xp_needed) * 100 if xp_needed > 0 else 100

        return {
            "level": level,
            "title": GamificationService.get_level_title(level),
            "current_xp": total_xp,
            "xp_in_level": xp_in_level,
            "xp_needed": xp_needed,
            "progress": min(progress, 100),
        }

    @staticmethod
    def get_level_title(level):
        try:
            return LevelTitle.objects.get(level=level).title
        except LevelTitle.DoesNotExist:
            titles = {
                1: "Yangi Talaba",
                2: "Izlovchi",
                3: "O'rganuvchi",
                5: "Bilimdon",
                8: "Ustoz Shogird",
                10: "Bilim Masteri",
                15: "Ilm Elchisi",
                20: "Akademik",
                30: "Grand Master",
            }
            return titles.get(level, f"Level {level}")

    @staticmethod
    @transaction.atomic
    def update_streak(user_id):
        streak, _ = Streak.objects.get_or_create(student_id=user_id)
        today = date.today()

        if streak.last_activity_date == today:
            return streak

        if streak.last_activity_date == today - timedelta(days=1):
            streak.current_streak += 1
        elif (
            streak.last_activity_date
            and streak.last_activity_date < today - timedelta(days=1)
        ):
            if streak.streak_freeze_count > 0:
                streak.streak_freeze_count -= 1
            else:
                streak.current_streak = 1

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_activity_date = today
        streak.save()

        GamificationService.check_and_award_badges(
            user_id, "streak_updated", {"streak": streak.current_streak}
        )

        if streak.current_streak in [7, 30, 100]:
            bonus_xp = {7: 25, 30: 100, 100: 500}.get(streak.current_streak, 0)
            GamificationService.award_xp(
                user_id,
                bonus_xp,
                "streak_bonus",
                f"{streak.current_streak} kunlik streak bonus",
            )

        return streak

    @staticmethod
    def check_and_award_badges(user_id, event_type, context=None):
        from apps.users.models import StudentProfile

        new_badges = []
        context = context or {}

        try:
            profile = StudentProfile.objects.get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return new_badges

        badges_to_check = Badge.objects.filter(is_active=True)

        for badge in badges_to_check:
            if UserBadge.objects.filter(student_id=user_id, badge=badge).exists():
                continue

            earned = False

            if badge.condition_type == "count":
                if event_type == "quiz_complete":
                    if profile.total_quizzes_completed >= badge.condition_value:
                        earned = True
                elif event_type == "lesson_complete":
                    pass

            elif badge.condition_type == "streak":
                if event_type == "streak_updated":
                    streak = context.get("streak", 0)
                    if streak >= badge.condition_value:
                        earned = True

            if earned:
                user_badge = UserBadge.objects.create(student_id=user_id, badge=badge)
                new_badges.append(user_badge)

                if badge.xp_bonus > 0:
                    GamificationService.award_xp(
                        user_id,
                        badge.xp_bonus,
                        "badge_earn",
                        f"{badge.name} badge uchun bonus",
                    )

                if badge.coin_bonus > 0:
                    profile.coins += badge.coin_bonus
                    profile.save()

        return new_badges

    @staticmethod
    def update_leaderboard(user_id, xp_amount=None):
        from apps.users.models import StudentProfile

        try:
            profile = StudentProfile.objects.get(user_id=user_id)
        except StudentProfile.DoesNotExist:
            return

        if xp_amount is None:
            xp_amount = profile.xp_points

        LeaderboardEntry.objects.update_or_create(
            student_id=user_id,
            classroom=None,
            period="all_time",
            defaults={"xp_points": profile.xp_points},
        )

        cache_key = f"leaderboard:all_time"
        try:
            from django_redis import get_redis_connection

            redis = get_redis_connection()
            redis.zadd(cache_key, {str(user_id): profile.xp_points})
        except:
            pass

    @staticmethod
    def get_leaderboard(period="weekly", classroom_id=None, limit=20):
        cache_key = f"leaderboard:{period}:class:{classroom_id or 'global'}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        from apps.users.serializers import UserPublicSerializer

        if classroom_id:
            from apps.classroom.models import Enrollment

            enrolled_students = Enrollment.objects.filter(
                classroom_id=classroom_id, is_active=True
            ).select_related("student", "student__student_profile")

            entries = []
            for enrollment in enrolled_students:
                profile = enrollment.student.student_profile
                entries.append(
                    {
                        "student": UserPublicSerializer(enrollment.student).data,
                        "xp_points": profile.xp_points,
                        "level": profile.level,
                    }
                )
        else:
            from apps.users.models import StudentProfile

            profiles = StudentProfile.objects.select_related("user").order_by(
                "-xp_points"
            )[:limit]
            entries = [
                {
                    "student": UserPublicSerializer(p.user).data,
                    "xp_points": p.xp_points,
                    "level": p.level,
                }
                for p in profiles
            ]

        for i, entry in enumerate(entries, 1):
            entry["rank"] = i

        cache.set(cache_key, entries, 300)
        return entries

    @staticmethod
    def claim_daily_bonus(user_id):
        today = date.today()
        cache_key = f"daily_bonus:{user_id}:{today}"

        if cache.get(cache_key):
            return {"claimed": False, "message": "Bugungi bonus allaqachon olingan"}

        bonus = 3
        GamificationService.award_xp(
            user_id, bonus, "daily_bonus", "Kunlik kirish bonusi"
        )
        GamificationService.update_streak(user_id)

        cache.set(cache_key, True, 86400)

        return {"claimed": True, "xp_earned": bonus}

    @staticmethod
    def generate_daily_quests(user_id):
        today = date.today()

        existing_quests = DailyQuest.objects.filter(student_id=user_id, date=today)
        if existing_quests.exists():
            return list(existing_quests)

        quests = [
            DailyQuest(
                student_id=user_id, quest_type="lesson", target_count=1, xp_reward=5
            ),
            DailyQuest(
                student_id=user_id, quest_type="quiz", target_count=1, xp_reward=10
            ),
            DailyQuest(
                student_id=user_id, quest_type="social", target_count=1, xp_reward=5
            ),
            DailyQuest(
                student_id=user_id, quest_type="streak", target_count=1, xp_reward=3
            ),
        ]

        DailyQuest.objects.bulk_create(quests)
        return quests

    @staticmethod
    def update_quest_progress(user_id, quest_type, increment=1):
        today = date.today()

        try:
            quest = DailyQuest.objects.get(
                student_id=user_id, quest_type=quest_type, date=today
            )
        except DailyQuest.DoesNotExist:
            return None

        if quest.is_completed:
            return quest

        quest.current_count += increment
        if quest.current_count >= quest.target_count:
            quest.is_completed = True
            quest.completed_at = timezone.now()
            quest.save()

            GamificationService.award_xp(
                user_id,
                quest.xp_reward,
                "quest_complete",
                f"Kunlik vazifa: {quest.get_quest_type_display()}",
            )

            all_completed = not DailyQuest.objects.filter(
                student_id=user_id, date=today, is_completed=False
            ).exists()

            if all_completed:
                GamificationService.award_xp(
                    user_id, 50, "daily_jackpot", "Barcha kunlik vazifalarni bajarish"
                )

        return quest
